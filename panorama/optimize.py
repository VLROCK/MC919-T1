"""Ajuste global: homografias no plano; rotações e foco nas superfícies curvas."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .geometry import intrinsic, project


def bundle(transforms, root, edges, frames, args):
    ids = sorted(transforms)
    variable = [i for i in ids if i != root]
    curved = args.projection != "planar"
    if curved:
        x0 = np.concatenate([Rotation.from_matrix(transforms[i]).as_rotvec() for i in variable]
                            + [np.array([np.log(args.focal_factor)])])
    else:
        x0 = np.concatenate([transforms[i].ravel()[:8] for i in variable])

    def unpack(x):
        ts = {root: np.eye(3)}
        for k, i in enumerate(variable):
            ts[i] = (Rotation.from_rotvec(x[k*3:k*3+3]).as_matrix() if curved else
                     np.r_[x[k*8:k*8+8], 1.].reshape(3, 3))
        return ts, np.exp(x[-1]) if curved else args.focal_factor

    # Amostragem uniforme determinística; todos os pares aceitos entram no custo.
    samples = [(e, np.linspace(0, len(e.a)-1, min(len(e.a), args.ba_points), dtype=int))
               for e in edges]

    def residual(x):
        ts, focal = unpack(x)
        Ks = {i: intrinsic(frames[i], focal) for i in ids} if curved else {}
        result = []
        for e, pick in samples:
            if curved:
                H = Ks[e.j] @ ts[e.j].T @ ts[e.i] @ np.linalg.inv(Ks[e.i])
            else:
                try:
                    H = np.linalg.solve(ts[e.j], ts[e.i])
                except np.linalg.LinAlgError:
                    return np.full(sum(4*len(s) for _, s in samples), 1e8)
            try:
                reverse = np.linalg.inv(H)
            except np.linalg.LinAlgError:
                return np.full(sum(4*len(s) for _, s in samples), 1e8)
            result.extend([(project(H, e.a[pick]) - e.b[pick]).ravel(),
                           (project(reverse, e.b[pick]) - e.a[pick]).ravel()])
        return np.concatenate(result)

    bounds = (np.full_like(x0, -np.inf), np.full_like(x0, np.inf))
    if curved:
        bounds[0][-1], bounds[1][-1] = np.log(.15), np.log(5.)
    before = residual(x0)
    fit = least_squares(residual, x0, loss="soft_l1", f_scale=args.ransac,
                        x_scale="jac", max_nfev=args.ba_iterations, bounds=bounds)
    after = residual(fit.x)
    accepted = bool(np.isfinite(after).all() and np.mean(after**2) <= np.mean(before**2))
    ts, focal = unpack(fit.x if accepted else x0)
    info = dict(model="rotation_shared_focal" if curved else "homography",
                accepted=accepted, converged=bool(fit.success), message=fit.message,
                evaluations=fit.nfev, initial_rmse_px=float(np.sqrt(np.mean(before**2)*2)),
                final_rmse_px=float(np.sqrt(np.mean(after**2)*2)),
                focal_factor=focal, sampled_pairs=len(samples))
    return ts, focal, info


def alignment_errors(transforms, edges, frames, projection, focal):
    rows = []
    for e in edges:
        if projection == "planar":
            H = np.linalg.solve(transforms[e.j], transforms[e.i])
        else:
            H = intrinsic(frames[e.j], focal) @ transforms[e.j].T @ transforms[e.i]
            H = H @ np.linalg.inv(intrinsic(frames[e.i], focal))
        residuals = project(H, e.a) - e.b
        rows.append(dict(i=e.i, j=e.j, mean_px=float(np.linalg.norm(residuals, axis=1).mean()),
                         rmse_px=float(np.sqrt(np.mean(np.sum(residuals**2, axis=1))))))
    return rows
