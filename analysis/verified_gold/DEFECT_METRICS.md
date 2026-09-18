# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.309 [0.237, 0.420] | 0.704 | 0.704 | 0.429 | 0.429 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.407 [0.286, 0.561] | 0.904 | 0.431 | 0.562 | 0.419 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.302 [0.224, 0.418] | 0.681 | 0.681 | 0.419 | 0.419 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.290 [0.241, 0.380] | 0.855 | 0.746 | 0.433 | 0.418 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.353, 0.490] | 0.660 | 0.435 | 0.494 | 0.414 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.444 [0.392, 0.550] | 0.911 | 0.387 | 0.598 | 0.414 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.463 [0.364, 0.630] | 0.926 | 0.369 | 0.617 | 0.411 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.272 [0.253, 0.299] | 0.917 | 0.800 | 0.419 | 0.406 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.321 [0.270, 0.403] | 0.732 | 0.547 | 0.446 | 0.405 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.259 [0.193, 0.349] | 0.955 | 0.894 | 0.408 | 0.402 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.451 [0.322, 0.640] | 0.924 | 0.361 | 0.606 | 0.401 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.438 [0.344, 0.579] | 0.899 | 0.368 | 0.589 | 0.400 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.265 [0.187, 0.400] | 1.000 | 0.754 | 0.420 | 0.393 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.457 [0.366, 0.633] | 0.779 | 0.344 | 0.576 | 0.393 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.272 [0.196, 0.390] | 0.957 | 0.657 | 0.423 | 0.384 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.284 [0.214, 0.404] | 0.582 | 0.582 | 0.382 | 0.382 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.389 [0.299, 0.533] | 0.787 | 0.373 | 0.521 | 0.381 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.235 [0.179, 0.314] | 0.974 | 0.950 | 0.378 | 0.376 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.414 [0.414, 0.414] | 0.667 | 0.343 | 0.511 | 0.375 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.259 [0.205, 0.361] | 0.955 | 0.667 | 0.408 | 0.373 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.278 [0.223, 0.364] | 0.865 | 0.556 | 0.421 | 0.370 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.259 [0.206, 0.350] | 0.933 | 0.646 | 0.406 | 0.370 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.284 [0.170, 0.445] | 0.687 | 0.511 | 0.402 | 0.365 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.265 [0.179, 0.420] | 0.768 | 0.581 | 0.394 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.432 [0.376, 0.517] | 0.579 | 0.306 | 0.495 | 0.358 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.426 [0.329, 0.620] | 0.697 | 0.307 | 0.529 | 0.357 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.395 [0.325, 0.529] | 0.604 | 0.325 | 0.478 | 0.357 |
| gpt-6-astra · compound-realistic · low | 6 | 0.247 [0.192, 0.370] | 0.800 | 0.625 | 0.377 | 0.354 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.426 [0.341, 0.573] | 0.585 | 0.301 | 0.493 | 0.353 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.247 [0.182, 0.327] | 0.976 | 0.615 | 0.394 | 0.352 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.833 | 0.357 | 0.488 | 0.351 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.235 [0.167, 0.367] | 0.905 | 0.679 | 0.373 | 0.349 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.210 [0.156, 0.276] | 1.000 | 0.971 | 0.347 | 0.345 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.235 [0.146, 0.382] | 0.844 | 0.644 | 0.367 | 0.344 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.358 [0.281, 0.490] | 0.753 | 0.328 | 0.485 | 0.342 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.364 [0.260, 0.526] | 0.766 | 0.317 | 0.494 | 0.339 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.346 [0.282, 0.472] | 0.800 | 0.329 | 0.483 | 0.337 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.259 [0.164, 0.376] | 0.712 | 0.477 | 0.380 | 0.336 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.345 [0.345, 0.345] | 0.588 | 0.303 | 0.435 | 0.323 |
| claude-opus-5 · compound-realistic · low | 6 | 0.383 [0.289, 0.533] | 0.590 | 0.273 | 0.464 | 0.319 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.222 [0.153, 0.331] | 0.720 | 0.562 | 0.340 | 0.319 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.191 [0.139, 0.261] | 0.969 | 0.939 | 0.320 | 0.318 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.448 [0.448, 0.448] | 0.565 | 0.245 | 0.500 | 0.317 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.222 [0.145, 0.345] | 0.706 | 0.537 | 0.338 | 0.314 |
| gpt-6-astra · compound-realistic · high | 6 | 0.204 [0.145, 0.310] | 0.805 | 0.688 | 0.325 | 0.314 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.241 [0.167, 0.356] | 0.722 | 0.429 | 0.361 | 0.308 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.488 [0.398, 0.610] | 0.491 | 0.220 | 0.489 | 0.303 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.210 [0.169, 0.275] | 0.810 | 0.523 | 0.333 | 0.300 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.309 [0.204, 0.468] | 0.562 | 0.281 | 0.398 | 0.294 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.346 [0.276, 0.458] | 0.629 | 0.250 | 0.446 | 0.290 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.191 [0.140, 0.282] | 0.838 | 0.564 | 0.312 | 0.286 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.147, 0.287] | 0.750 | 0.478 | 0.320 | 0.286 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.305 [0.245, 0.414] | 0.521 | 0.263 | 0.385 | 0.282 |
| claude-opus-5 · compound-realistic · high | 6 | 0.364 [0.290, 0.496] | 0.484 | 0.230 | 0.415 | 0.282 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.160 [0.097, 0.256] | 0.963 | 0.743 | 0.275 | 0.264 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.526 | 0.213 | 0.417 | 0.263 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.173 [0.135, 0.217] | 0.933 | 0.538 | 0.292 | 0.262 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.167 [0.123, 0.232] | 0.659 | 0.574 | 0.266 | 0.258 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.160 [0.093, 0.244] | 0.812 | 0.650 | 0.268 | 0.257 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.142 [0.077, 0.228] | 1.000 | 1.000 | 0.249 | 0.249 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.167 [0.103, 0.244] | 0.711 | 0.482 | 0.270 | 0.248 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.130 [0.076, 0.206] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.130 [0.096, 0.178] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.130 [0.097, 0.181] | 1.000 | 1.000 | 0.230 | 0.230 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.222 [0.178, 0.300] | 0.480 | 0.237 | 0.304 | 0.229 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.130 [0.086, 0.208] | 0.955 | 0.955 | 0.228 | 0.228 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.123 [0.071, 0.189] | 0.952 | 0.952 | 0.219 | 0.219 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.136 [0.082, 0.213] | 0.759 | 0.524 | 0.230 | 0.216 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.222 [0.162, 0.315] | 0.387 | 0.198 | 0.282 | 0.209 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.117 [0.073, 0.163] | 0.864 | 0.322 | 0.207 | 0.172 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.105 [0.042, 0.182] | 0.708 | 0.378 | 0.183 | 0.164 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.080 [0.042, 0.147] | 0.722 | 0.325 | 0.144 | 0.129 |

MRV-vs-CE: 5/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.309 [0.237, 0.420] | 0.704 | 0.704 | 0.429 | 0.429 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.407 [0.286, 0.561] | 0.904 | 0.431 | 0.562 | 0.419 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.302 [0.224, 0.417] | 0.681 | 0.681 | 0.419 | 0.419 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.290 [0.241, 0.385] | 0.855 | 0.746 | 0.433 | 0.418 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.353, 0.486] | 0.660 | 0.435 | 0.494 | 0.414 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.444 [0.392, 0.550] | 0.911 | 0.387 | 0.598 | 0.414 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.463 [0.364, 0.628] | 0.926 | 0.369 | 0.617 | 0.411 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.272 [0.253, 0.299] | 0.917 | 0.800 | 0.419 | 0.406 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.321 [0.269, 0.410] | 0.732 | 0.547 | 0.446 | 0.405 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.259 [0.192, 0.347] | 0.955 | 0.894 | 0.408 | 0.402 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.451 [0.326, 0.640] | 0.924 | 0.361 | 0.606 | 0.401 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.438 [0.347, 0.580] | 0.899 | 0.368 | 0.589 | 0.400 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.265 [0.189, 0.400] | 1.000 | 0.754 | 0.420 | 0.393 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.457 [0.367, 0.633] | 0.779 | 0.344 | 0.576 | 0.393 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.272 [0.193, 0.387] | 0.957 | 0.657 | 0.423 | 0.384 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.284 [0.214, 0.404] | 0.582 | 0.582 | 0.382 | 0.382 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.389 [0.299, 0.533] | 0.787 | 0.373 | 0.521 | 0.381 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.235 [0.180, 0.314] | 0.974 | 0.950 | 0.378 | 0.376 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.414 [0.414, 0.414] | 0.667 | 0.343 | 0.511 | 0.375 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.259 [0.205, 0.361] | 0.955 | 0.667 | 0.408 | 0.373 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.278 [0.224, 0.369] | 0.865 | 0.556 | 0.421 | 0.370 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.259 [0.207, 0.350] | 0.933 | 0.646 | 0.406 | 0.370 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.284 [0.171, 0.444] | 0.687 | 0.511 | 0.402 | 0.365 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.265 [0.176, 0.420] | 0.768 | 0.581 | 0.394 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.432 [0.376, 0.517] | 0.579 | 0.306 | 0.495 | 0.358 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.426 [0.331, 0.620] | 0.697 | 0.307 | 0.529 | 0.357 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.395 [0.322, 0.525] | 0.604 | 0.325 | 0.478 | 0.357 |
| gpt-6-astra · compound-realistic · low | 6 | 0.247 [0.192, 0.370] | 0.800 | 0.625 | 0.377 | 0.354 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.426 [0.341, 0.573] | 0.585 | 0.301 | 0.493 | 0.353 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.247 [0.183, 0.329] | 0.976 | 0.615 | 0.394 | 0.352 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.833 | 0.357 | 0.488 | 0.351 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.235 [0.167, 0.368] | 0.905 | 0.679 | 0.373 | 0.349 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.210 [0.156, 0.276] | 1.000 | 0.971 | 0.347 | 0.345 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.235 [0.146, 0.365] | 0.844 | 0.644 | 0.367 | 0.344 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.358 [0.278, 0.490] | 0.753 | 0.328 | 0.485 | 0.342 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.364 [0.260, 0.525] | 0.766 | 0.317 | 0.494 | 0.339 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.346 [0.282, 0.471] | 0.800 | 0.329 | 0.483 | 0.337 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.259 [0.164, 0.371] | 0.712 | 0.477 | 0.380 | 0.336 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.345 [0.345, 0.345] | 0.588 | 0.303 | 0.435 | 0.323 |
| claude-opus-5 · compound-realistic · low | 6 | 0.383 [0.290, 0.530] | 0.590 | 0.273 | 0.464 | 0.319 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.222 [0.153, 0.337] | 0.720 | 0.562 | 0.340 | 0.319 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.191 [0.140, 0.260] | 0.969 | 0.939 | 0.320 | 0.318 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.448 [0.448, 0.448] | 0.565 | 0.245 | 0.500 | 0.317 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.222 [0.145, 0.354] | 0.706 | 0.537 | 0.338 | 0.314 |
| gpt-6-astra · compound-realistic · high | 6 | 0.204 [0.145, 0.311] | 0.805 | 0.688 | 0.325 | 0.314 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.241 [0.169, 0.361] | 0.722 | 0.429 | 0.361 | 0.308 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.488 [0.398, 0.610] | 0.491 | 0.220 | 0.489 | 0.303 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.210 [0.169, 0.277] | 0.810 | 0.523 | 0.333 | 0.300 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.309 [0.205, 0.470] | 0.562 | 0.281 | 0.398 | 0.294 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.346 [0.276, 0.459] | 0.629 | 0.250 | 0.446 | 0.290 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.191 [0.140, 0.282] | 0.838 | 0.564 | 0.312 | 0.286 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.147, 0.287] | 0.750 | 0.478 | 0.320 | 0.286 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.305 [0.245, 0.414] | 0.521 | 0.263 | 0.385 | 0.282 |
| claude-opus-5 · compound-realistic · high | 6 | 0.364 [0.282, 0.496] | 0.484 | 0.230 | 0.415 | 0.282 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.160 [0.095, 0.256] | 0.963 | 0.743 | 0.275 | 0.264 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.526 | 0.213 | 0.417 | 0.263 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.173 [0.135, 0.218] | 0.933 | 0.538 | 0.292 | 0.262 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.167 [0.122, 0.232] | 0.659 | 0.574 | 0.266 | 0.258 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.160 [0.092, 0.245] | 0.812 | 0.650 | 0.268 | 0.257 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.142 [0.077, 0.226] | 1.000 | 1.000 | 0.249 | 0.249 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.167 [0.103, 0.244] | 0.711 | 0.482 | 0.270 | 0.248 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.130 [0.076, 0.204] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.130 [0.096, 0.178] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.130 [0.097, 0.182] | 1.000 | 1.000 | 0.230 | 0.230 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.222 [0.178, 0.301] | 0.480 | 0.237 | 0.304 | 0.229 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.130 [0.085, 0.208] | 0.955 | 0.955 | 0.228 | 0.228 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.123 [0.071, 0.188] | 0.952 | 0.952 | 0.219 | 0.219 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.136 [0.082, 0.213] | 0.759 | 0.524 | 0.230 | 0.216 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.222 [0.160, 0.311] | 0.387 | 0.198 | 0.282 | 0.209 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.117 [0.074, 0.163] | 0.864 | 0.322 | 0.207 | 0.172 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.105 [0.042, 0.181] | 0.708 | 0.378 | 0.183 | 0.164 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.080 [0.042, 0.146] | 0.722 | 0.325 | 0.144 | 0.129 |

MRV-vs-CE: 5/21 pairs resolve positive on ΔF1'.

