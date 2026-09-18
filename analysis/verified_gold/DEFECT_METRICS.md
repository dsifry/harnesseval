# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.338 [0.261, 0.458] | 0.704 | 0.704 | 0.457 | 0.457 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.324 [0.230, 0.454] | 0.676 | 0.676 | 0.438 | 0.438 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.297 [0.244, 0.375] | 0.846 | 0.733 | 0.440 | 0.423 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.466 [0.422, 0.552] | 0.908 | 0.377 | 0.616 | 0.417 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.270 [0.208, 0.351] | 0.952 | 0.889 | 0.421 | 0.415 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.405 [0.368, 0.489] | 0.645 | 0.420 | 0.498 | 0.412 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.277 [0.254, 0.312] | 0.911 | 0.788 | 0.425 | 0.410 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.297 [0.213, 0.433] | 0.957 | 0.657 | 0.454 | 0.409 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.473 [0.388, 0.612] | 0.921 | 0.354 | 0.625 | 0.405 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.399 [0.272, 0.557] | 0.894 | 0.404 | 0.551 | 0.401 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.466 [0.349, 0.630] | 0.920 | 0.348 | 0.619 | 0.399 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.304 [0.230, 0.420] | 0.577 | 0.577 | 0.398 | 0.398 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.318 [0.260, 0.400] | 0.712 | 0.522 | 0.439 | 0.395 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.304 [0.244, 0.397] | 0.865 | 0.556 | 0.450 | 0.393 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.439 [0.338, 0.604] | 0.890 | 0.348 | 0.588 | 0.388 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.264 [0.196, 0.389] | 1.000 | 0.736 | 0.417 | 0.388 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.243 [0.182, 0.319] | 0.973 | 0.947 | 0.389 | 0.387 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.277 [0.224, 0.354] | 0.932 | 0.641 | 0.427 | 0.387 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.270 [0.217, 0.378] | 0.952 | 0.656 | 0.421 | 0.383 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.405 [0.323, 0.532] | 0.779 | 0.361 | 0.533 | 0.382 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.284 [0.183, 0.454] | 0.764 | 0.575 | 0.414 | 0.380 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.453 [0.352, 0.639] | 0.761 | 0.322 | 0.568 | 0.376 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.297 [0.184, 0.458] | 0.677 | 0.500 | 0.413 | 0.373 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.250 [0.183, 0.375] | 0.902 | 0.673 | 0.392 | 0.365 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.223 [0.167, 0.297] | 1.000 | 0.971 | 0.365 | 0.363 |
| gpt-6-astra · compound-realistic · low | 6 | 0.257 [0.210, 0.359] | 0.792 | 0.613 | 0.388 | 0.362 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.419 [0.353, 0.532] | 0.596 | 0.318 | 0.492 | 0.362 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.257 [0.190, 0.348] | 0.974 | 0.603 | 0.406 | 0.360 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.453 [0.394, 0.541] | 0.568 | 0.296 | 0.504 | 0.358 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.446 [0.357, 0.583] | 0.574 | 0.292 | 0.502 | 0.353 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.439 [0.354, 0.611] | 0.684 | 0.294 | 0.535 | 0.352 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.236 [0.154, 0.363] | 0.833 | 0.625 | 0.368 | 0.343 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.209 [0.150, 0.296] | 0.969 | 0.939 | 0.344 | 0.343 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.378 [0.277, 0.537] | 0.757 | 0.306 | 0.505 | 0.338 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.365 [0.285, 0.489] | 0.740 | 0.312 | 0.489 | 0.336 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.351 [0.296, 0.464] | 0.788 | 0.313 | 0.486 | 0.331 |
| gpt-6-astra · compound-realistic · high | 6 | 0.216 [0.155, 0.333] | 0.800 | 0.681 | 0.340 | 0.328 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.250 [0.156, 0.364] | 0.685 | 0.446 | 0.366 | 0.320 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.230 [0.155, 0.342] | 0.694 | 0.523 | 0.345 | 0.319 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.223 [0.152, 0.339] | 0.702 | 0.541 | 0.338 | 0.316 |
| claude-opus-5 · compound-realistic · low | 6 | 0.392 [0.293, 0.536] | 0.574 | 0.260 | 0.466 | 0.313 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.520 [0.417, 0.631] | 0.484 | 0.216 | 0.502 | 0.305 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.216 [0.158, 0.314] | 0.800 | 0.508 | 0.340 | 0.303 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.236 [0.163, 0.346] | 0.700 | 0.402 | 0.354 | 0.298 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.203 [0.151, 0.295] | 0.833 | 0.556 | 0.326 | 0.297 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.372 [0.300, 0.474] | 0.625 | 0.247 | 0.466 | 0.296 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.209 [0.157, 0.274] | 0.738 | 0.463 | 0.326 | 0.288 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.311 [0.212, 0.469] | 0.541 | 0.264 | 0.395 | 0.286 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.320 [0.250, 0.444] | 0.511 | 0.255 | 0.393 | 0.284 |
| claude-opus-5 · compound-realistic · high | 6 | 0.378 [0.302, 0.505] | 0.471 | 0.220 | 0.419 | 0.279 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.169 [0.105, 0.270] | 0.962 | 0.735 | 0.287 | 0.275 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.182 [0.145, 0.231] | 0.931 | 0.529 | 0.305 | 0.271 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.176 [0.133, 0.242] | 0.650 | 0.565 | 0.277 | 0.268 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.162 [0.100, 0.241] | 0.800 | 0.632 | 0.270 | 0.258 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.142 [0.103, 0.200] | 1.000 | 1.000 | 0.249 | 0.249 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.243 [0.192, 0.324] | 0.480 | 0.237 | 0.323 | 0.240 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.162 [0.105, 0.236] | 0.686 | 0.453 | 0.262 | 0.239 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.135 [0.078, 0.221] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.135 [0.101, 0.196] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.135 [0.077, 0.216] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.135 [0.078, 0.206] | 0.952 | 0.952 | 0.237 | 0.237 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.135 [0.090, 0.225] | 0.952 | 0.952 | 0.237 | 0.237 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.149 [0.088, 0.241] | 0.759 | 0.524 | 0.249 | 0.232 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.223 [0.164, 0.319] | 0.367 | 0.184 | 0.277 | 0.202 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.128 [0.079, 0.178] | 0.864 | 0.322 | 0.224 | 0.184 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.115 [0.045, 0.206] | 0.708 | 0.378 | 0.198 | 0.176 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.088 [0.048, 0.158] | 0.722 | 0.325 | 0.157 | 0.138 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.338 [0.260, 0.458] | 0.704 | 0.704 | 0.457 | 0.457 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.324 [0.230, 0.454] | 0.676 | 0.676 | 0.438 | 0.438 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.297 [0.244, 0.375] | 0.846 | 0.733 | 0.440 | 0.423 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.466 [0.422, 0.552] | 0.908 | 0.377 | 0.616 | 0.417 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.270 [0.205, 0.351] | 0.952 | 0.889 | 0.421 | 0.415 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.405 [0.368, 0.490] | 0.645 | 0.420 | 0.498 | 0.412 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.277 [0.255, 0.312] | 0.911 | 0.788 | 0.425 | 0.410 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.297 [0.209, 0.433] | 0.957 | 0.657 | 0.454 | 0.409 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.473 [0.388, 0.611] | 0.921 | 0.354 | 0.625 | 0.405 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.399 [0.272, 0.554] | 0.894 | 0.404 | 0.551 | 0.401 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.466 [0.350, 0.630] | 0.920 | 0.348 | 0.619 | 0.399 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.304 [0.231, 0.420] | 0.577 | 0.577 | 0.398 | 0.398 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.318 [0.260, 0.403] | 0.712 | 0.522 | 0.439 | 0.395 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.304 [0.244, 0.400] | 0.865 | 0.556 | 0.450 | 0.393 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.439 [0.338, 0.604] | 0.890 | 0.348 | 0.588 | 0.388 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.264 [0.196, 0.389] | 1.000 | 0.736 | 0.417 | 0.388 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.243 [0.183, 0.319] | 0.973 | 0.947 | 0.389 | 0.387 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.277 [0.225, 0.354] | 0.932 | 0.641 | 0.427 | 0.387 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.270 [0.217, 0.378] | 0.952 | 0.656 | 0.421 | 0.383 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.405 [0.322, 0.532] | 0.779 | 0.361 | 0.533 | 0.382 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.284 [0.182, 0.454] | 0.764 | 0.575 | 0.414 | 0.380 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.453 [0.356, 0.639] | 0.761 | 0.322 | 0.568 | 0.376 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.297 [0.184, 0.456] | 0.677 | 0.500 | 0.413 | 0.373 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.250 [0.184, 0.375] | 0.902 | 0.673 | 0.392 | 0.365 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.223 [0.167, 0.297] | 1.000 | 0.971 | 0.365 | 0.363 |
| gpt-6-astra · compound-realistic · low | 6 | 0.257 [0.210, 0.362] | 0.792 | 0.613 | 0.388 | 0.362 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.419 [0.351, 0.532] | 0.596 | 0.318 | 0.492 | 0.362 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.257 [0.190, 0.348] | 0.974 | 0.603 | 0.406 | 0.360 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.453 [0.394, 0.542] | 0.568 | 0.296 | 0.504 | 0.358 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.446 [0.354, 0.583] | 0.574 | 0.292 | 0.502 | 0.353 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.439 [0.354, 0.611] | 0.684 | 0.294 | 0.535 | 0.352 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.236 [0.154, 0.362] | 0.833 | 0.625 | 0.368 | 0.343 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.209 [0.152, 0.296] | 0.969 | 0.939 | 0.344 | 0.343 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.378 [0.275, 0.537] | 0.757 | 0.306 | 0.505 | 0.338 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.365 [0.285, 0.485] | 0.740 | 0.312 | 0.489 | 0.336 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.351 [0.298, 0.458] | 0.788 | 0.313 | 0.486 | 0.331 |
| gpt-6-astra · compound-realistic · high | 6 | 0.216 [0.155, 0.333] | 0.800 | 0.681 | 0.340 | 0.328 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.250 [0.156, 0.363] | 0.685 | 0.446 | 0.366 | 0.320 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.230 [0.155, 0.351] | 0.694 | 0.523 | 0.345 | 0.319 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.223 [0.152, 0.347] | 0.702 | 0.541 | 0.338 | 0.316 |
| claude-opus-5 · compound-realistic · low | 6 | 0.392 [0.293, 0.536] | 0.574 | 0.260 | 0.466 | 0.313 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.520 [0.420, 0.631] | 0.484 | 0.216 | 0.502 | 0.305 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.216 [0.158, 0.320] | 0.800 | 0.508 | 0.340 | 0.303 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.236 [0.162, 0.347] | 0.700 | 0.402 | 0.354 | 0.298 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.203 [0.150, 0.299] | 0.833 | 0.556 | 0.326 | 0.297 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.372 [0.298, 0.486] | 0.625 | 0.247 | 0.466 | 0.296 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.209 [0.156, 0.276] | 0.738 | 0.463 | 0.326 | 0.288 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.311 [0.212, 0.469] | 0.541 | 0.264 | 0.395 | 0.286 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.320 [0.250, 0.444] | 0.511 | 0.255 | 0.393 | 0.284 |
| claude-opus-5 · compound-realistic · high | 6 | 0.378 [0.293, 0.505] | 0.471 | 0.220 | 0.419 | 0.279 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.169 [0.102, 0.268] | 0.962 | 0.735 | 0.287 | 0.275 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.182 [0.145, 0.232] | 0.931 | 0.529 | 0.305 | 0.271 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.176 [0.131, 0.242] | 0.650 | 0.565 | 0.277 | 0.268 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.162 [0.098, 0.241] | 0.800 | 0.632 | 0.270 | 0.258 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.142 [0.103, 0.200] | 1.000 | 1.000 | 0.249 | 0.249 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.243 [0.193, 0.326] | 0.480 | 0.237 | 0.323 | 0.240 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.162 [0.104, 0.236] | 0.686 | 0.453 | 0.262 | 0.239 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.135 [0.078, 0.221] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.135 [0.101, 0.196] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.135 [0.077, 0.216] | 1.000 | 1.000 | 0.238 | 0.238 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.135 [0.078, 0.206] | 0.952 | 0.952 | 0.237 | 0.237 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.135 [0.090, 0.223] | 0.952 | 0.952 | 0.237 | 0.237 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.149 [0.088, 0.241] | 0.759 | 0.524 | 0.249 | 0.232 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.223 [0.162, 0.317] | 0.367 | 0.184 | 0.277 | 0.202 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.128 [0.079, 0.178] | 0.864 | 0.322 | 0.224 | 0.184 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.115 [0.045, 0.206] | 0.708 | 0.378 | 0.198 | 0.176 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.088 [0.048, 0.156] | 0.722 | 0.325 | 0.157 | 0.138 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

