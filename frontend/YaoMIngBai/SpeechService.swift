import AVFoundation

final class SpeechService: NSObject {
    static let shared = SpeechService()
    private let synthesizer = AVSpeechSynthesizer()

    private override init() {
        super.init()
    }

    func speak(_ text: String, rate: Float = 0.48) {
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
        utterance.rate = rate
        utterance.pitchMultiplier = 1.0
        synthesizer.speak(utterance)
    }

    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
    }
}
