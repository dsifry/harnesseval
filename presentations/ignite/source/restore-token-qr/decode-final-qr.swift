import Foundation
import ImageIO
import Vision
let path = "/Users/dsifry/Documents/Codex/2026-09-28/we-a/work/restore-token-qr/delivery-images/delivery-images.020.png"
let source = CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil)!
let cg = CGImageSourceCreateImageAtIndex(source,0,nil)!
let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]
try VNImageRequestHandler(cgImage:cg,options:[:]).perform([request])
let decoded = request.results?.compactMap{$0.payloadStringValue} ?? []
guard decoded == ["https://dsifry.github.io/harnesseval"] else { fatalError("Unexpected QR: \(decoded)") }
print("Native closing-slide PNG QR verified: \(decoded[0])")
