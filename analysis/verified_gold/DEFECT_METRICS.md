# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.345 [0.267, 0.467] | 0.704 | 0.704 | 0.463 | 0.463 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.331 [0.234, 0.463] | 0.676 | 0.676 | 0.444 | 0.444 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.303 [0.248, 0.389] | 0.846 | 0.733 | 0.447 | 0.429 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.276 [0.211, 0.361] | 0.952 | 0.889 | 0.428 | 0.421 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.476 [0.433, 0.552] | 0.908 | 0.377 | 0.624 | 0.421 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.414 [0.376, 0.495] | 0.645 | 0.420 | 0.504 | 0.417 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.283 [0.257, 0.322] | 0.911 | 0.788 | 0.432 | 0.416 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.303 [0.215, 0.444] | 0.957 | 0.657 | 0.461 | 0.415 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.483 [0.397, 0.622] | 0.921 | 0.354 | 0.633 | 0.408 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.310 [0.233, 0.435] | 0.577 | 0.577 | 0.404 | 0.404 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.476 [0.356, 0.634] | 0.920 | 0.348 | 0.627 | 0.402 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.400 [0.275, 0.558] | 0.892 | 0.400 | 0.552 | 0.400 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.324 [0.263, 0.413] | 0.712 | 0.522 | 0.445 | 0.400 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.310 [0.247, 0.409] | 0.865 | 0.556 | 0.457 | 0.398 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.269 [0.198, 0.397] | 1.000 | 0.736 | 0.424 | 0.394 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.248 [0.186, 0.323] | 0.973 | 0.947 | 0.396 | 0.393 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.283 [0.229, 0.362] | 0.932 | 0.641 | 0.434 | 0.392 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.448 [0.343, 0.620] | 0.890 | 0.348 | 0.596 | 0.392 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.276 [0.219, 0.385] | 0.952 | 0.656 | 0.428 | 0.388 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.414 [0.332, 0.537] | 0.779 | 0.361 | 0.541 | 0.386 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.290 [0.188, 0.463] | 0.764 | 0.575 | 0.420 | 0.385 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.462 [0.358, 0.653] | 0.761 | 0.322 | 0.575 | 0.380 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.303 [0.186, 0.463] | 0.677 | 0.500 | 0.419 | 0.378 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.255 [0.188, 0.378] | 0.902 | 0.673 | 0.398 | 0.370 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.228 [0.169, 0.306] | 1.000 | 0.971 | 0.371 | 0.369 |
| gpt-6-astra · compound-realistic · low | 6 | 0.262 [0.216, 0.365] | 0.792 | 0.613 | 0.394 | 0.367 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.262 [0.193, 0.363] | 0.974 | 0.603 | 0.413 | 0.365 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.428 [0.363, 0.536] | 0.596 | 0.318 | 0.498 | 0.365 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.462 [0.402, 0.548] | 0.568 | 0.296 | 0.510 | 0.361 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.448 [0.363, 0.617] | 0.684 | 0.294 | 0.542 | 0.355 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.214 [0.152, 0.307] | 0.969 | 0.939 | 0.350 | 0.348 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.241 [0.157, 0.375] | 0.833 | 0.625 | 0.374 | 0.348 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.441 [0.348, 0.583] | 0.566 | 0.286 | 0.496 | 0.347 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.386 [0.282, 0.558] | 0.757 | 0.306 | 0.511 | 0.341 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.372 [0.292, 0.495] | 0.740 | 0.312 | 0.495 | 0.340 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.359 [0.305, 0.469] | 0.788 | 0.313 | 0.493 | 0.334 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| gpt-6-astra · compound-realistic · high | 6 | 0.221 [0.159, 0.337] | 0.800 | 0.681 | 0.346 | 0.333 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.255 [0.158, 0.377] | 0.685 | 0.446 | 0.372 | 0.325 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.234 [0.158, 0.349] | 0.694 | 0.523 | 0.351 | 0.324 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.228 [0.154, 0.352] | 0.702 | 0.541 | 0.344 | 0.320 |
| claude-opus-5 · compound-realistic · low | 6 | 0.400 [0.298, 0.547] | 0.574 | 0.260 | 0.472 | 0.315 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.221 [0.160, 0.326] | 0.800 | 0.508 | 0.346 | 0.308 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.241 [0.165, 0.355] | 0.700 | 0.402 | 0.359 | 0.302 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.207 [0.152, 0.304] | 0.833 | 0.556 | 0.331 | 0.302 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.517 [0.408, 0.633] | 0.478 | 0.211 | 0.497 | 0.300 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.379 [0.305, 0.484] | 0.625 | 0.247 | 0.472 | 0.299 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.214 [0.159, 0.283] | 0.738 | 0.463 | 0.332 | 0.292 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.317 [0.217, 0.469] | 0.541 | 0.264 | 0.400 | 0.288 |
| claude-opus-5 · compound-realistic · high | 6 | 0.386 [0.306, 0.519] | 0.471 | 0.220 | 0.424 | 0.281 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.172 [0.106, 0.277] | 0.962 | 0.735 | 0.292 | 0.279 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.186 [0.148, 0.239] | 0.931 | 0.529 | 0.310 | 0.276 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.311 [0.234, 0.444] | 0.500 | 0.247 | 0.383 | 0.275 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.179 [0.135, 0.247] | 0.650 | 0.565 | 0.281 | 0.272 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.166 [0.101, 0.250] | 0.800 | 0.632 | 0.274 | 0.262 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.145 [0.105, 0.208] | 1.000 | 1.000 | 0.253 | 0.253 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.166 [0.105, 0.245] | 0.686 | 0.453 | 0.267 | 0.242 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.248 [0.195, 0.333] | 0.480 | 0.237 | 0.327 | 0.242 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.138 [0.079, 0.226] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.138 [0.102, 0.203] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.138 [0.078, 0.226] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.138 [0.092, 0.232] | 0.952 | 0.952 | 0.241 | 0.241 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.152 [0.089, 0.250] | 0.759 | 0.524 | 0.253 | 0.235 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.131 [0.078, 0.202] | 0.950 | 0.950 | 0.230 | 0.230 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.228 [0.167, 0.324] | 0.367 | 0.184 | 0.281 | 0.204 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.131 [0.079, 0.183] | 0.864 | 0.322 | 0.228 | 0.186 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.110 [0.033, 0.215] | 0.696 | 0.364 | 0.190 | 0.169 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.090 [0.050, 0.159] | 0.722 | 0.325 | 0.160 | 0.141 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.345 [0.267, 0.468] | 0.704 | 0.704 | 0.463 | 0.463 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.331 [0.234, 0.463] | 0.676 | 0.676 | 0.444 | 0.444 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.303 [0.249, 0.389] | 0.846 | 0.733 | 0.447 | 0.429 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.276 [0.211, 0.361] | 0.952 | 0.889 | 0.428 | 0.421 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.476 [0.433, 0.552] | 0.908 | 0.377 | 0.624 | 0.421 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.414 [0.376, 0.495] | 0.645 | 0.420 | 0.504 | 0.417 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.283 [0.258, 0.322] | 0.911 | 0.788 | 0.432 | 0.416 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.303 [0.213, 0.444] | 0.957 | 0.657 | 0.461 | 0.415 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.483 [0.397, 0.622] | 0.921 | 0.354 | 0.633 | 0.408 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.310 [0.233, 0.435] | 0.577 | 0.577 | 0.404 | 0.404 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.476 [0.358, 0.634] | 0.920 | 0.348 | 0.627 | 0.402 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.400 [0.275, 0.556] | 0.892 | 0.400 | 0.552 | 0.400 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.324 [0.263, 0.415] | 0.712 | 0.522 | 0.445 | 0.400 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.310 [0.247, 0.409] | 0.865 | 0.556 | 0.457 | 0.398 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.269 [0.199, 0.397] | 1.000 | 0.736 | 0.424 | 0.394 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.248 [0.187, 0.323] | 0.973 | 0.947 | 0.396 | 0.393 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.283 [0.229, 0.361] | 0.932 | 0.641 | 0.434 | 0.392 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.448 [0.346, 0.620] | 0.890 | 0.348 | 0.596 | 0.392 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.276 [0.219, 0.385] | 0.952 | 0.656 | 0.428 | 0.388 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.414 [0.330, 0.537] | 0.779 | 0.361 | 0.541 | 0.386 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.290 [0.186, 0.456] | 0.764 | 0.575 | 0.420 | 0.385 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.462 [0.360, 0.653] | 0.761 | 0.322 | 0.575 | 0.380 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.303 [0.189, 0.463] | 0.677 | 0.500 | 0.419 | 0.378 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.255 [0.189, 0.376] | 0.902 | 0.673 | 0.398 | 0.370 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.228 [0.170, 0.306] | 1.000 | 0.971 | 0.371 | 0.369 |
| gpt-6-astra · compound-realistic · low | 6 | 0.262 [0.216, 0.365] | 0.792 | 0.613 | 0.394 | 0.367 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.262 [0.193, 0.363] | 0.974 | 0.603 | 0.413 | 0.365 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.428 [0.361, 0.533] | 0.596 | 0.318 | 0.498 | 0.365 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.462 [0.402, 0.548] | 0.568 | 0.296 | 0.510 | 0.361 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.448 [0.364, 0.617] | 0.684 | 0.294 | 0.542 | 0.355 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.214 [0.155, 0.307] | 0.969 | 0.939 | 0.350 | 0.348 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.241 [0.157, 0.371] | 0.833 | 0.625 | 0.374 | 0.348 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.441 [0.344, 0.583] | 0.566 | 0.286 | 0.496 | 0.347 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.386 [0.279, 0.557] | 0.757 | 0.306 | 0.511 | 0.341 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.372 [0.291, 0.495] | 0.740 | 0.312 | 0.495 | 0.340 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.359 [0.305, 0.467] | 0.788 | 0.313 | 0.493 | 0.334 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| gpt-6-astra · compound-realistic · high | 6 | 0.221 [0.159, 0.341] | 0.800 | 0.681 | 0.346 | 0.333 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.255 [0.158, 0.377] | 0.685 | 0.446 | 0.372 | 0.325 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.234 [0.158, 0.354] | 0.694 | 0.523 | 0.351 | 0.324 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.228 [0.154, 0.355] | 0.702 | 0.541 | 0.344 | 0.320 |
| claude-opus-5 · compound-realistic · low | 6 | 0.400 [0.300, 0.547] | 0.574 | 0.260 | 0.472 | 0.315 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.221 [0.160, 0.331] | 0.800 | 0.508 | 0.346 | 0.308 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.241 [0.165, 0.355] | 0.700 | 0.402 | 0.359 | 0.302 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.207 [0.152, 0.305] | 0.833 | 0.556 | 0.331 | 0.302 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.517 [0.410, 0.633] | 0.478 | 0.211 | 0.497 | 0.300 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.379 [0.303, 0.487] | 0.625 | 0.247 | 0.472 | 0.299 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.214 [0.158, 0.283] | 0.738 | 0.463 | 0.332 | 0.292 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.317 [0.217, 0.474] | 0.541 | 0.264 | 0.400 | 0.288 |
| claude-opus-5 · compound-realistic · high | 6 | 0.386 [0.297, 0.517] | 0.471 | 0.220 | 0.424 | 0.281 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.172 [0.104, 0.277] | 0.962 | 0.735 | 0.292 | 0.279 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.186 [0.147, 0.239] | 0.931 | 0.529 | 0.310 | 0.276 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.311 [0.234, 0.444] | 0.500 | 0.247 | 0.383 | 0.275 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.179 [0.133, 0.247] | 0.650 | 0.565 | 0.281 | 0.272 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.166 [0.100, 0.250] | 0.800 | 0.632 | 0.274 | 0.262 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.145 [0.105, 0.208] | 1.000 | 1.000 | 0.253 | 0.253 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.166 [0.104, 0.245] | 0.686 | 0.453 | 0.267 | 0.242 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.248 [0.195, 0.333] | 0.480 | 0.237 | 0.327 | 0.242 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.138 [0.079, 0.226] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.138 [0.102, 0.202] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.138 [0.078, 0.226] | 1.000 | 1.000 | 0.242 | 0.242 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.138 [0.092, 0.229] | 0.952 | 0.952 | 0.241 | 0.241 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.152 [0.089, 0.250] | 0.759 | 0.524 | 0.253 | 0.235 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.131 [0.078, 0.200] | 0.950 | 0.950 | 0.230 | 0.230 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.228 [0.166, 0.323] | 0.367 | 0.184 | 0.281 | 0.204 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.131 [0.079, 0.183] | 0.864 | 0.322 | 0.228 | 0.186 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.110 [0.033, 0.215] | 0.696 | 0.364 | 0.190 | 0.169 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.090 [0.050, 0.158] | 0.722 | 0.325 | 0.160 | 0.141 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

