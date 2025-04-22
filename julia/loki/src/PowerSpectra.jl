module PowerSpectra

using FFTW: fftn, fftshift
using LinearAlgebra: sum, abs2

function _compute_radial_grid(shape::NTuple{3, Int})
    k_center = [(n - 1) / 2 for n in shape]
    grid_kx = Array{Float64, 3}(undef, shape...)
    grid_ky = similar(grid_kx)
    grid_kz = similar(grid_kx)
    for z in 1:shape[3], y in 1:shape[2], x in 1:shape[1]
        grid_kx[x, y, z] = x - 1 - k_center[1]
        grid_ky[x, y, z] = y - 1 - k_center[2]
        grid_kz[x, y, z] = z - 1 - k_center[3]
    end
    return sqrt.(grid_kx.^2 .+ grid_ky.^2 .+ grid_kz.^2)
end

function _compute_3d_power_spectrum(field::Array{<:Real})
    @assert ndims(field) >= 3 "Field should have at least 3 spatial dimensions."
    spacial_dims = (ndims(field)-2):ndims(field)
    fft_field = fftshift(fftn(field, dims=spacial_dims)) ./ sqrt(prod(size(field, d) for d in spacial_dims))
    spectrum = sum(abs2.(fft_field), dims=1:(ndims(field)-3)) |> dropdims
    return spectrum
end

function _compute_spherical_integration(spectrum_3d::Array{Float64, 3})
    num_k_modes = Int(floor(minimum(size(spectrum_3d)) / 2))
    k_bin_edges = range(0.5, stop=num_k_modes, length=num_k_modes+1)
    k_bin_centers = ceil.((k_bin_edges[1:end-1] .+ k_bin_edges[2:end]) ./ 2)
    grid_k_magn = _compute_radial_grid(size(spectrum_3d))
    bin_indices = map(x -> searchsortedfirst(k_bin_edges, x), grid_k_magn)
    spectrum_1d = zeros(Float64, num_k_modes)
    for (i, val) in enumerate(spectrum_3d)
        bin = bin_indices[i]
        if 1 <= bin <= num_k_modes
            spectrum_1d[bin] += val
        end
    end
    return k_bin_centers, spectrum_1d
end

function compute_1d_power_spectrum(field::Array{<:Real})
    spectrum_3d = _compute_3d_power_spectrum(field)
    return _compute_spherical_integration(spectrum_3d)
end

end # module