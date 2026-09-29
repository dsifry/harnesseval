import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root='/Users/dsifry/Documents/Codex/2026-09-28/we-a';
const skill='/Users/dsifry/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
await finalizePresentation({workspaceDir:root,candidatePath:path.join(root,'work/deck/keynote-candidate-v9.pptx'),finalPath:path.join(root,'outputs/DaveSifry_VibesVsEvidence_v9.pptx'),pythonExecutable:'/Users/dsifry/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),explicitTotalSlideCount:20,requiredNativeChartOwnerSlides:[3,4,5,7,10,11,12,13,14],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Helvetica Neue']},layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit'],verifyArtifactToolImport:true,receiptPath:path.join(root,'work/deck/keynote-v9-validation.json')});
console.log('Native-compatible deck passed validation.');
