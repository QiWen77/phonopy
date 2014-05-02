import numpy as np
from anharmonic.phonon3.conductivity import Conductivity
from anharmonic.phonon3.collision_matrix import CollisionMatrix
from anharmonic.phonon3.triplets import get_grid_points_by_rotations
from anharmonic.file_IO import write_kappa_to_hdf5, write_collision_to_hdf5, read_collision_from_hdf5
from phonopy.units import THzToEv, Kb

def get_thermal_conductivity_LBTE(
        interaction,
        symmetry,
        temperatures=np.arange(0, 1001, 10, dtype='double'),
        sigmas=[],
        mass_variances=None,
        grid_points=None,
        cutoff_lifetime=1e-4, # in second
        gv_delta_q=1e-4, # for group velocity
        write_gamma=False,
        read_gamma=False,
        input_filename=None,
        output_filename=None,
        log_level=0):

    if log_level:
        print "-------------------- Lattice thermal conducitivity (LBTE) --------------------"
        lbte = Conductivity_LBTE(interaction,
                                 symmetry,
                                 grid_points=grid_points,
                                 temperatures=temperatures,
                                 sigmas=sigmas,
                                 mass_variances=mass_variances,
                                 cutoff_lifetime=cutoff_lifetime,
                                 gv_delta_q=gv_delta_q,
                                 log_level=log_level)

    if read_gamma:
        if not _set_collision_from_file(lbte, filename=input_filename):
            print "Reading collisions failed."
            return False
        
    for i in lbte:
        if write_gamma:
            _write_collision(lbte, i=i, filename=output_filename)

    _write_collision(lbte, filename=output_filename)
        
    if grid_points is None:
        lbte.set_kappa_at_sigmas()
        _write_kappa(lbte, filename=output_filename, log_level=log_level)
    
    return lbte

def _write_collision(lbte, i=None, filename=None):
    temperatures = lbte.get_temperatures()
    sigmas = lbte.get_sigmas()
    gamma = lbte.get_gamma()
    gamma_isotope = lbte.get_gamma_isotope()
    collision_matrix = lbte.get_collision_matrix()
    mesh = lbte.get_mesh_numbers()
    
    if i is not None:
        gp = lbte.get_grid_points()[i]
        for j, sigma in enumerate(sigmas):
            if gamma_isotope is not None:
                gamma_isotope_at_sigma = gamma_isotope[j, i]
            else:
                gamma_isotope_at_sigma = None
            write_collision_to_hdf5(temperatures,
                                    mesh,
                                    gamma=gamma[j, :, i],
                                    gamma_isotope=gamma_isotope_at_sigma,
                                    collision_matrix=collision_matrix[j, :, i],
                                    grid_point=gp,
                                    sigma=sigma,
                                    filename=filename)
    else:    
        for j, sigma in enumerate(sigmas):
            if gamma_isotope is not None:
                gamma_isotope_at_sigma = gamma_isotope[j]
            else:
                gamma_isotope_at_sigma = None
            write_collision_to_hdf5(temperatures,
                                    mesh,
                                    gamma=gamma[j],
                                    gamma_isotope=gamma_isotope_at_sigma,
                                    collision_matrix=collision_matrix[j],
                                    sigma=sigma,
                                    filename=filename)
    
def _write_kappa(lbte, filename=None, log_level=0):
    temperatures = lbte.get_temperatures()
    sigmas = lbte.get_sigmas()
    mesh = lbte.get_mesh_numbers()
    frequencies = lbte.get_frequencies()
    gv = lbte.get_group_velocities()
    qpoints = lbte.get_qpoints()
    kappa = lbte.get_kappa()
    
    for i, sigma in enumerate(sigmas):
        kappa_at_sigma = kappa[i]
        if log_level:
            print "----------- Thermal conductivity (W/m-k)",
            if sigma:
                print "for sigma=%s -----------" % sigma
            else:
                print "with tetrahedron method -----------"
            print ("#%6s     " + " %-9s" * 6) % ("T(K)", "xx", "yy", "zz",
                                                "yz", "xz", "xy")
            for t, k in zip(temperatures, kappa_at_sigma):
                print ("%7.1f" + " %9.3f" * 6) % ((t,) + tuple(k))
            print
        write_kappa_to_hdf5(temperatures,
                            mesh,
                            frequency=frequencies,
                            group_velocity=gv,
                            kappa=kappa_at_sigma,
                            qpoint=qpoints,
                            sigma=sigma,
                            filename=filename)

def _set_collision_from_file(lbte, filename=None):
    sigmas = lbte.get_sigmas()
    mesh = lbte.get_mesh_numbers()
    grid_points = lbte.get_grid_points()
    temperatures = lbte.get_temperatures()
    num_band = lbte.get_frequencies().shape[1]

    gamma = np.zeros((len(sigmas),
                      len(temperatures),
                      len(grid_points),
                      num_band), dtype='double')
    collision_matrix = np.zeros(
            (len(sigmas),
             len(temperatures),
             len(grid_points), num_band, 3,
             len(grid_points), num_band, 3),
            dtype='double')
    gamma_iso = np.zeros((len(sigmas),
                          len(grid_points),
                          num_band), dtype='double')
    is_isotope = False

    for j, sigma in enumerate(sigmas):
        collisions = read_collision_from_hdf5(mesh,
                                              sigma=sigma,
                                              filename=filename)
        if collisions is False:
            gamma_iso_gps
            for i, gp in enumerate(grid_points):
                collision_gp = read_collision_from_hdf5(
                    mesh,
                    grid_point=gp,
                    sigma=sigma,
                    filename=filename)
                if collision_gp is False:
                    print "Gamma at grid point %d doesn't exist." % gp
                    return False
                else:
                    (collision_matrix_at_sigma,
                     gamma_at_sigma,
                     gamma_isotope_at_sigma) = collisions_gp
                    collision_matrix[j, :, i] = collision_matrix_at_sigma
                    gamma[j, :, i] = gamma_at_sigma
                    if gamma_isotope_at_sigma is not None:
                        is_isotope = True
                        gamma_iso[j, :, i] = gamma_isotope_at_sigma
        else:            
            (collision_matrix_at_sigma,
             gamma_at_sigma,
             gamma_isotope_at_sigma) = collisions
            collision_matrix[j] = collision_matrix_at_sigma
            gamma[j] = gamma_at_sigma
            if gamma_isotope_at_sigma is not None:
                is_isotope = True
                gamma_iso[j] = gamma_isotope_at_sigma
        
    lbte.set_gamma(gamma)
    lbte.set_collision_matrix(collision_matrix)
    # if is_isotope:
    #     lbte.set_gamma_isotope(gamma_iso)

    return True

        
class Conductivity_LBTE(Conductivity):
    def __init__(self,
                 interaction,
                 symmetry,
                 grid_points=None,
                 temperatures=np.arange(0, 1001, 10, dtype='double'),
                 sigmas=[],
                 mass_variances=None,
                 cutoff_lifetime=1e-4, # in second
                 gv_delta_q=None, # finite difference for group veolocity
                 log_level=0):
        self._pp = None
        self._temperatures = None
        self._sigmas = None
        self._no_kappa_stars = None
        self._gv_delta_q = None
        self._log_level = None
        self._primitive = None
        self._dm = None
        self._frequency_factor_to_THz = None
        self._cutoff_frequency = None
        self._cutoff_lifetime = None

        self._symmetry = None
        self._point_operations = None
        self._rotations_cartesian = None
        
        self._grid_points = None
        self._grid_weights = None
        self._grid_address = None
        self._ir_grid_points = None
        self._ir_grid_weights = None

        self._gamma = None
        self._collision_matrix = None
        self._read_gamma = False
        self._read_gamma_iso = False
        self._read_collision_matrix = False
        self._frequencies = None
        self._gv = None
        self._gamma_iso = None

        self._mesh = None
        self._coarse_mesh = None
        self._coarse_mesh_shifts = None
        self._conversion_factor = None
        
        self._isotope = None
        self._mass_variances = None
        self._grid_point_count = None

        Conductivity.__init__(self,
                              interaction,
                              symmetry,
                              grid_points=grid_points,
                              temperatures=temperatures,
                              sigmas=sigmas,
                              mass_variances=mass_variances,
                              cutoff_lifetime=cutoff_lifetime,
                              gv_delta_q=gv_delta_q,
                              log_level=log_level)

        self._allocate_values()
        
    def set_kappa_at_sigmas(self):
        if len(self._grid_points) != len(self._ir_grid_points):
            print "Collision matrix is not well created."
            import sys
            sys.exit(1)

        # self._collision_matrix is overwritten to save memory space
        self._combine_collisions()
            
        num_band = self._primitive.get_number_of_atoms() * 3
        num_ir_grid_points = len(self._ir_grid_points)

        weights = []
        for r_gps in self._rot_grid_points:
            weights.append(np.sqrt(len(np.unique(r_gps))) / np.sqrt(len(r_gps)))

        for i, j in list(np.ndindex((len(weights), len(weights)))):
            self._collision_matrix[:, :, i, :, :, j, :, :] *= (
                weights[i] * weights[j])

        for j, sigma in enumerate(self._sigmas):
            for k, t in enumerate(self._temperatures):
                if t > 0:
                    X = self._get_X(t, weights)
                    kappa = self._get_kappa(
                        self._collision_matrix[j, k].reshape(
                            num_ir_grid_points * num_band * 3,
                            num_ir_grid_points * num_band * 3),
                        X, t)
                    self._kappa[j, k] = [
                        kappa[0, 0], kappa[1, 1], kappa[2, 2],
                        kappa[1, 2], kappa[0, 2], kappa[0, 1]]

    def set_collision_matrix(self, collision_matrix):
        self._collision_matrix = collision_matrix
        self._read_collision_matrix = True
        
    def get_collision_matrix(self):
        return self._collision_matrix
                
    def _run_at_grid_point(self):
        i = self._grid_point_count
        self._show_log_header(i)
        grid_point = self._grid_points[i]

        if not self._read_gamma:
            self._collision.set_grid_point(grid_point)
            
            if self._log_level:
                print "Number of triplets:",
                print len(self._pp.get_triplets_at_q()[0])
                print "Calculating interaction..."
                
            self._collision.run_interaction()
            self._set_collision_matrix_at_sigmas(i)
            
        if self._isotope is not None:
            self._set_gamma_isotope_at_sigmas(i)

        self._set_gv(i)
        self._show_log(i)

    def _allocate_values(self):
        num_band = self._primitive.get_number_of_atoms() * 3
        num_grid_points = len(self._grid_points)
        num_ir_grid_points = len(self._ir_grid_points)

        self._kappa = np.zeros((len(self._sigmas),
                                len(self._temperatures),
                                6), dtype='double')
        self._collision_matrix = np.zeros(
            (len(self._sigmas),
             len(self._temperatures),
             num_grid_points, num_band, 3,
             num_ir_grid_points, num_band, 3),
            dtype='double')
        self._gv = np.zeros((num_grid_points,
                             num_band,
                             3), dtype='double')
        self._gamma = np.zeros((len(self._sigmas),
                                len(self._temperatures),
                                num_grid_points,
                                num_band), dtype='double')
        if self._isotope is not None:
            self._gamma_iso = np.zeros((len(self._sigmas),
                                        num_grid_points,
                                        num_band), dtype='double')
        self._rot_grid_points = np.zeros(
            (len(self._ir_grid_points), len(self._point_operations)),
            dtype='intc')
        for i, ir_gp in enumerate(self._ir_grid_points):
            self._rot_grid_points[i] = get_grid_points_by_rotations(
                ir_gp,
                self._point_operations,
                self._mesh)
        self._collision = CollisionMatrix(self._pp,
                                          self._point_operations,
                                          self._ir_grid_points,
                                          self._rot_grid_points)

    def _set_collision_matrix_at_sigmas(self, i):
        for j, sigma in enumerate(self._sigmas):
            if self._log_level:
                print "Calculating collision matrix with",
                if sigma is None:
                    print "tetrahedron method"
                else:
                    print "sigma=%s" % sigma
            self._collision.set_sigma(sigma)
            self._collision.set_integration_weights()
            for k, t in enumerate(self._temperatures):
                self._collision.set_temperature(t)
                self._collision.run()
                self._gamma[j, k, i] = self._collision.get_imag_self_energy()
                self._collision_matrix[j, k, i] = (
                    self._collision.get_collision_matrix())

    def _combine_collisions(self):
        # Include main diagonal part
        num_band = self._primitive.get_number_of_atoms() * 3
        for j, k in list(np.ndindex((len(self._sigmas),
                                     len(self._temperatures)))):
            for i, ir_gp in enumerate(self._ir_grid_points):
                r_gps = self._rot_grid_points[i]
                for r, r_gp in zip(self._rotations_cartesian, r_gps):
                    if r_gp != ir_gp:
                        continue

                    main_diagonal = self._gamma[j, k, i].copy()
                    if self._gamma_iso is not None:
                        main_diagonal += self._gamma_iso[j, i]
                        
                    for l in range(num_band):
                        self._collision_matrix[
                            j, k, i, l, :, i, l, :] += main_diagonal[l] * r
                
    def _get_X(self, t, weights):
        X = self._gv.copy()
        freqs = self._frequencies[self._ir_grid_points]
        sinh = np.where(freqs > self._cutoff_frequency,
                        np.sinh(freqs * THzToEv / (2 * Kb * t)),
                        -1)
        inv_sinh = np.where(sinh > 0, 1 / sinh, 0)
        freqs_sinh = freqs * THzToEv * inv_sinh / (4 * Kb * t ** 2)
        num_band = self._primitive.get_number_of_atoms() * 3
                
        for i, f in enumerate(freqs_sinh):
            X[i] *= weights[i]
            for j in range(num_band):
                X[i, j] *= f[j]
        
        if t > 0:
            return X.reshape(-1, 3)
        else:
            return np.zeros_like(self._gv.reshape(-1, 3))

    def _get_kappa(self, col_mat, X, t, pinv_cutoff=1e-11):
        num_ir_grid_points = len(self._ir_grid_points)
        num_band = self._primitive.get_number_of_atoms() * 3
        rot_order = len(self._rotations_cartesian)
        w, v = np.linalg.eigh((col_mat + col_mat.T) / 2)
        e = np.zeros(len(w), dtype='double')
        for l, val in enumerate(w):
            if val > pinv_cutoff:
                e[l] = 1 / val
        inv_col = np.dot(v, (e * v).T)
        # inv_col = np.dot(v, np.dot(np.diag(e), v.T))
        
        Y = np.dot(inv_col, X.ravel()).reshape(-1, 3)
        RX = np.dot(self._rotations_cartesian.reshape(-1, 3), X.T).T
        RY = np.dot(self._rotations_cartesian.reshape(-1, 3), Y.T).T
        
        sum_outer = np.zeros((3, 3), dtype='double')
        for irX, irY in zip(
                RX.reshape(num_ir_grid_points, num_band, rot_order, 3),
                RY.reshape(num_ir_grid_points, num_band, rot_order, 3)):
            for X_band, Y_band in zip(irX, irY):
                for RX_band, RY_band in zip(X_band, Y_band):
                    sum_outer += np.outer(RX_band, RY_band)
        
        return (sum_outer * self._conversion_factor * 2 * Kb * t ** 2 /
                np.prod(self._mesh))
                    
    def _show_log(self, i):
        q = self._qpoints[i]
        gp = self._grid_points[i]
        frequencies = self._frequencies[gp]
        gv = self._gv[i]

        print "Frequency, projected group velocity (x, y, z), group velocity norm",
        if self._gv_delta_q is None:
            print
        else:
            print " (dq=%3.1e)" % self._gv_delta_q
        for f, v in zip(frequencies, gv):
            print "%8.3f   (%8.3f %8.3f %8.3f) %8.3f" % (
                f, v[0], v[1], v[2], np.linalg.norm(v))

