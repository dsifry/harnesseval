import Foundation
import AppKit
import CoreImage
import Vision
let url = "https://dsifry.github.io/harnesseval"
let filter = CIFilter(name: "CIQRCodeGenerator")!
filter.setValue(Data(url.utf8), forKey: "inputMessage")
filter.setValue("H", forKey: "inputCorrectionLevel")
let code = filter.outputImage!
let side = code.extent.width + 8
let white = CIImage(color: CIColor.white).cropped(to: CGRect(x:0,y:0,width:side,height:side))
let padded = code.transformed(by:CGAffineTransform(translationX:4,y:4)).composited(over:white).cropped(to:white.extent)
let scaled = padded.transformed(by:CGAffineTransform(scaleX:16,y:16))
let cg = CIContext(options:[.useSoftwareRenderer:true]).createCGImage(scaled,from:scaled.extent)!
let png = NSBitmapImageRep(cgImage:cg).representation(using:.png,properties:[:])!
let path=URL(fileURLWithPath:"/Users/dsifry/Documents/Codex/2026-09-28/we-a/outputs/assets/Full_Report_QR.png")
try png.write(to:path)
let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]
try VNImageRequestHandler(cgImage:cg,options:[:]).perform([request])
let decoded = request.results?.compactMap{$0.payloadStringValue} ?? []
guard decoded == [url] else { fatalError("QR did not decode to requested URL: \(decoded)") }
print("Verified QR: \(decoded[0]); \(cg.width)x\(cg.height); 4-module quiet zone; ECC H")
