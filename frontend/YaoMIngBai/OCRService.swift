import UIKit
import Vision
import ImageIO

enum OCRServiceError: Error {
    case missingCGImage
}

final class OCRService {
    static let shared = OCRService()

    private init() {}

    func recognizeText(
        from image: UIImage
    ) async throws -> String {
        let normalizedImage = image.normalizedForOCR()

        guard let cgImage = normalizedImage.cgImage else {
            throw OCRServiceError.missingCGImage
        }

        return try await withCheckedThrowingContinuation {
            continuation in

            let request = VNRecognizeTextRequest {
                request,
                error in

                if let error {
                    continuation.resume(
                        throwing: error
                    )
                    return
                }

                let observations =
                    request.results
                    as? [VNRecognizedTextObservation]
                    ?? []

                /*
                 Vision 返回顺序不一定符合说明书阅读顺序。
                 先按从上到下排序，同一行再从左到右排序。
                 */
                let sortedObservations = observations.sorted {
                    first,
                    second in

                    let verticalDifference = abs(
                        first.boundingBox.midY
                        - second.boundingBox.midY
                    )

                    if verticalDifference > 0.025 {
                        return first.boundingBox.midY
                            > second.boundingBox.midY
                    }

                    return first.boundingBox.minX
                        < second.boundingBox.minX
                }

                let recognizedLines =
                    sortedObservations.compactMap {
                        observation -> String? in

                        let candidates =
                            observation.topCandidates(3)

                        guard let candidate =
                            candidates.first(
                                where: {
                                    $0.confidence >= 0.35
                                }
                            )
                        else {
                            return nil
                        }

                        let line = candidate.string
                            .replacingOccurrences(
                                of: "\u{3000}",
                                with: " "
                            )
                            .trimmingCharacters(
                                in: .whitespacesAndNewlines
                            )

                        return line.isEmpty
                            ? nil
                            : line
                    }

                let text = recognizedLines.joined(
                    separator: "\n"
                )

                continuation.resume(
                    returning: text
                )
            }

            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true

            /*
             适当过滤过小的背景文字。
             小字漏识别时可改回 0.008。
             */
            request.minimumTextHeight = 0.012

            if #available(iOS 16.0, *) {
                request.revision =
                    VNRecognizeTextRequestRevision3
            }

            request.recognitionLanguages = [
                "zh-Hans",
                "zh-Hant",
                "en-US",
            ]

            let handler = VNImageRequestHandler(
                cgImage: cgImage,
                orientation: .up,
                options: [:]
            )

            DispatchQueue.global(
                qos: .userInitiated
            ).async {
                do {
                    try handler.perform([request])
                } catch {
                    continuation.resume(
                        throwing: error
                    )
                }
            }
        }
    }
}

private extension CGImagePropertyOrientation {
    init(_ orientation: UIImage.Orientation) {
        switch orientation {
        case .up:
            self = .up
        case .upMirrored:
            self = .upMirrored
        case .down:
            self = .down
        case .downMirrored:
            self = .downMirrored
        case .left:
            self = .left
        case .leftMirrored:
            self = .leftMirrored
        case .right:
            self = .right
        case .rightMirrored:
            self = .rightMirrored
        @unknown default:
            self = .up
        }
    }
}

private extension UIImage {
    /// 统一图片方向、背景和尺寸，再交给 Vision。
    func normalizedForOCR(
        maxDimension: CGFloat = 2200
    ) -> UIImage {
        let longestSide = max(
            size.width,
            size.height
        )

        guard longestSide > 0 else {
            return self
        }

        let scaleRatio = min(
            1,
            maxDimension / longestSide
        )

        let targetSize = CGSize(
            width: size.width * scaleRatio,
            height: size.height * scaleRatio
        )

        let format =
            UIGraphicsImageRendererFormat.default()

        format.scale = 1
        format.opaque = true

        return UIGraphicsImageRenderer(
            size: targetSize,
            format: format
        ).image { context in
            UIColor.white.setFill()

            context.fill(
                CGRect(
                    origin: .zero,
                    size: targetSize
                )
            )

            draw(
                in: CGRect(
                    origin: .zero,
                    size: targetSize
                )
            )
        }
    }
}