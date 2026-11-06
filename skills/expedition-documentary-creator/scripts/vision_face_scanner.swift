import Foundation
import AVFoundation
import Vision
import CoreGraphics

struct FrameDetection: Codable {
    let t: Double
    let faces: [[Double]]   // [x, y, w, h] normalized 0..1 (top-left origin)
    let humans: [[Double]]  // [x, y, w, h] normalized 0..1 (top-left origin)
}

struct ClipReport: Codable {
    let file: String
    let duration: Double
    let samples: [FrameDetection]
}

func scanVideo(path: String, stepSec: Double) -> ClipReport? {
    let url = URL(fileURLWithPath: path)
    let asset = AVURLAsset(url: url)
    let dur = CMTimeGetSeconds(asset.duration)
    if dur.isNaN || dur <= 0.4 { return nil }

    let gen = AVAssetImageGenerator(asset: asset)
    gen.appliesPreferredTrackTransform = true
    gen.maximumSize = CGSize(width: 640, height: 360)
    gen.requestedTimeToleranceBefore = CMTime(seconds: 0.25, preferredTimescale: 600)
    gen.requestedTimeToleranceAfter = CMTime(seconds: 0.25, preferredTimescale: 600)

    var samples: [FrameDetection] = []
    var t = 0.2
    while t < dur {
        let cmTime = CMTime(seconds: t, preferredTimescale: 600)
        if let cgImg = try? gen.copyCGImage(at: cmTime, actualTime: nil) {
            let faceReq = VNDetectFaceRectanglesRequest()
            faceReq.usesCPUOnly = true
            let humanReq = VNDetectHumanRectanglesRequest()
            humanReq.upperBodyOnly = true
            humanReq.usesCPUOnly = true
            let handler = VNImageRequestHandler(cgImage: cgImg, options: [:])
            try? handler.perform([faceReq, humanReq])

            var faceBoxes: [[Double]] = []
            if let results = faceReq.results {
                for r in results {
                    let b = r.boundingBox
                    // Convert Vision bottom-left origin to top-left origin
                    let x = Double(b.origin.x)
                    let y = Double(1.0 - b.origin.y - b.size.height)
                    let w = Double(b.size.width)
                    let h = Double(b.size.height)
                    faceBoxes.append([
                        (x * 1000).rounded() / 1000,
                        (y * 1000).rounded() / 1000,
                        (w * 1000).rounded() / 1000,
                        (h * 1000).rounded() / 1000
                    ])
                }
            }

            var humanBoxes: [[Double]] = []
            if let hResults = humanReq.results {
                for r in hResults where r.confidence > 0.65 {
                    let b = r.boundingBox
                    let x = Double(b.origin.x)
                    let y = Double(1.0 - b.origin.y - b.size.height)
                    let w = Double(b.size.width)
                    let h = Double(b.size.height)
                    humanBoxes.append([
                        (x * 1000).rounded() / 1000,
                        (y * 1000).rounded() / 1000,
                        (w * 1000).rounded() / 1000,
                        (h * 1000).rounded() / 1000
                    ])
                }
            }
            samples.append(FrameDetection(t: (t * 100).rounded() / 100, faces: faceBoxes, humans: humanBoxes))
        }
        t += stepSec
    }

    return ClipReport(
        file: (path as NSString).lastPathComponent,
        duration: (dur * 100).rounded() / 100,
        samples: samples
    )
}

let args = CommandLine.arguments
if args.count < 2 {
    fputs("Usage: vision_face_scanner <video_dir_or_file> [step_sec]\n", stderr)
    exit(1)
}
let target = args[1]
let stepSec = args.count >= 3 ? (Double(args[2]) ?? 1.0) : 1.0

var isDir: ObjCBool = false
FileManager.default.fileExists(atPath: target, isDirectory: &isDir)

var reports: [ClipReport] = []
if isDir.boolValue {
    let items = (try? FileManager.default.contentsOfDirectory(atPath: target))?.sorted() ?? []
    for item in items where item.lowercased().hasSuffix(".mp4") && !item.hasPrefix(".") {
        let full = (target as NSString).appendingPathComponent(item)
        if let rep = scanVideo(path: full, stepSec: stepSec) {
            reports.append(rep)
            fputs("Scanned \(item) (\(rep.duration)s)\n", stderr)
        }
    }
} else {
    if let rep = scanVideo(path: target, stepSec: stepSec) {
        reports.append(rep)
    }
}

let enc = JSONEncoder()
if let data = try? enc.encode(reports), let s = String(data: data, encoding: .utf8) {
    print(s)
}
