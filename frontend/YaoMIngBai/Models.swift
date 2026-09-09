import Foundation

enum AppTab: String, CaseIterable, Hashable {
    case home, scan, box, family, me

    var title: String {
        switch self {
        case .home: return "首页"
        case .scan: return "识别"
        case .box: return "家庭药箱"
        case .family: return "家人"
        case .me: return "我的"
        }
    }

    var icon: String {
        switch self {
        case .home: return "house.fill"
        case .scan: return "camera.viewfinder"
        case .box: return "shippingbox.fill"
        case .family: return "person.3.fill"
        case .me: return "person.crop.circle.fill"
        }
    }
}

enum Route: Hashable {
    case addMedicine
    case medicineCard
    case reminderSetting
    case reminderList
    case medicationAlarm
    case familyBox
    case medicineDetail
    case familyMembers
    case elderStatus
    case childFeedingRecord(memberName: String)
    case medicationRecords
    case profileSettings

    case elderHome
    case elderAlarm
    case elderMedicineDetail
    case elderMyMedicines
    case elderMissedDose
    case elderContactFamily
    case elderSettings
}

struct FamilyMember: Identifiable, Hashable {
    let id = UUID()
    var backendID: Int? = nil
    var emoji: String
    var name: String
    var role: String
    var status: String
    var age: String
    var weight: String
    var allergy: String
}

extension FamilyMember {
    var isChildProfile: Bool {
        let childKeywords = ["儿童", "孩子", "小宝", "宝宝", "婴幼儿"]
        if childKeywords.contains(where: { role.contains($0) || name.contains($0) }) || emoji == "👶" {
            return true
        }

        let trimmedAge = age.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let regex = try? NSRegularExpression(pattern: #"\d+(?:\.\d+)?"#),
              let match = regex.firstMatch(
                in: trimmedAge,
                range: NSRange(trimmedAge.startIndex..<trimmedAge.endIndex, in: trimmedAge)
              ),
              let range = Range(match.range, in: trimmedAge),
              let years = Double(trimmedAge[range]) else { return false }
        return years < 18
    }
}
struct Medicine: Identifiable, Hashable {
    let id = UUID()
    var backendID: Int? = nil
    var emoji: String
    var name: String
    var spec: String
    var category: String
    var owner: String
    var dose: String
    var frequency: String
    var mealTime: String
    var method: String
    /// 保存入家庭药箱后表示家里的实际存放位置；识别阶段可临时承载说明书里的贮藏提示，保存时必须由用户重新选择。
    var location: String
    /// 包装上标注的生产日期，格式为 yyyy-MM-dd。
    var productionDate: String = ""
    /// 包装或说明书标注的保质期长度，例如“36个月”。
    var shelfLife: String = ""
    /// 最终到期日期；不能把“36个月”等时长直接存入该字段。
    var expiry: String
    var stock: String
    var status: String
    var risks: [String]
    var contraindications: [String] = []
    var precautions: [String] = []
    var fallbackFields: [String] = []
    var needsConfirmation: Bool = true
    var note: String
    var originalText: String
    var speechText: String = ""
    var usedSampleFallback: Bool = false
    var demoOnly: Bool = false

/// 后端提取出的有效期完整原文。
    var expiryText: String = ""

/// 老人模式专用的精简播报文本。
    var elderSpeechText: String = ""

/// 当前数据来源，真实 OCR 时为 ocr。
    var dataSource: String = "ocr"

/// 后端解析质量：good、partial、poor。
    var parseQuality: String = "partial"

/// OCR 中没有成功解析出的核心字段。
    var missingFields: [String] = []
}


struct MedicineStockAmount: Hashable {
    var quantity: Double
    var unit: String
}

extension Medicine {
    var expiryDisplayText: String {
        let finalDate = expiry.trimmingCharacters(in: .whitespacesAndNewlines)
        if !finalDate.isEmpty { return finalDate }
        return shelfLife.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var displayStatus: String {
        let trimmed = status.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return "正常" }
        if trimmed == "待核对" || trimmed == "待确认" { return "需确认" }
        return trimmed
    }

    var needsAttention: Bool {
        displayStatus.contains("过期")
            || displayStatus.contains("不足")
            || displayStatus.contains("少")
            || displayStatus.contains("确认")
            || !risks.isEmpty
    }

    var groupingKey: String {
        [Self.normalized(name), owner.trimmingCharacters(in: .whitespacesAndNewlines), location.trimmingCharacters(in: .whitespacesAndNewlines), spec.trimmingCharacters(in: .whitespacesAndNewlines)]
            .joined(separator: "|")
    }

    var stockAmount: MedicineStockAmount? {
        Self.stockAmount(from: stock)
    }

    static func normalized(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: " ", with: "")
            .lowercased()
    }

    static func firstNumber(in text: String) -> Double? {
        guard let regex = try? NSRegularExpression(pattern: #"[0-9]+(?:\.[0-9]+)?"#) else { return nil }
        let nsText = text as NSString
        let range = NSRange(location: 0, length: nsText.length)
        guard let match = regex.firstMatch(in: text, range: range) else { return nil }
        return Double(nsText.substring(with: match.range))
    }

    static func stockAmount(from text: String) -> MedicineStockAmount? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty,
              let regex = try? NSRegularExpression(pattern: #"([0-9]+(?:\.[0-9]+)?)(\s*[^0-9\s/，,。；;]*)"#) else { return nil }
        let nsText = trimmed as NSString
        let range = NSRange(location: 0, length: nsText.length)
        guard let match = regex.firstMatch(in: trimmed, range: range),
              match.numberOfRanges >= 3,
              let quantity = Double(nsText.substring(with: match.range(at: 1))) else { return nil }
        let unit = nsText.substring(with: match.range(at: 2)).trimmingCharacters(in: .whitespacesAndNewlines)
        return MedicineStockAmount(quantity: quantity, unit: unit.isEmpty ? "份" : unit)
    }

    static func doseQuantity(from text: String) -> Double {
        firstNumber(in: text) ?? 1
    }

    func adjustedStock(by delta: Double) -> String {
        guard let regex = try? NSRegularExpression(pattern: #"[0-9]+(?:\.[0-9]+)?"#) else { return stock }
        let nsText = stock as NSString
        let range = NSRange(location: 0, length: nsText.length)
        guard let match = regex.firstMatch(in: stock, range: range),
              let quantity = Double(nsText.substring(with: match.range)) else { return stock }

        let updated = max(0, quantity + delta)
        let replacement: String
        if updated.rounded() == updated {
            replacement = String(Int(updated))
        } else {
            replacement = String(format: "%.1f", updated)
        }

        let mutable = NSMutableString(string: stock)
        mutable.replaceCharacters(in: match.range, with: replacement)
        return mutable as String
    }

    static func mergedStocks(_ stocks: [String]) -> String {
        let amounts = stocks.compactMap { stockAmount(from: $0) }
        if amounts.isEmpty {
            let nonEmpty = stocks.first { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
            return nonEmpty ?? "未填写"
        }

        let firstUnit = amounts.first?.unit ?? "份"
        if amounts.allSatisfy({ $0.unit == firstUnit }) {
            let total = amounts.reduce(0) { $0 + $1.quantity }
            let number = total.rounded() == total ? String(Int(total)) : String(format: "%.1f", total)
            return "\(number) \(firstUnit)"
        }

        return "\(stocks.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.count) 份库存"
    }
}


struct ReminderPlan: Identifiable, Hashable {
    let id = UUID()
    var backendID: Int? = nil
    var medicineBackendID: Int? = nil
    var medicineName: String
    var memberName: String
    var time: String
    var mealLabel: String
    var dose: String
    var status: String
    var isActive: Bool = true
}

struct DoseRecord: Identifiable, Hashable {
    let id = UUID()
    var backendID: Int? = nil
    var reminderBackendID: Int? = nil
    var medicineBackendID: Int? = nil
    var memberBackendID: Int? = nil
    var medicineName: String = ""
    var memberName: String = ""
    var dose: String = ""
    var recordedBy: String = ""
    var temperature: String = ""
    var note: String = ""
    var time: String
    var title: String
    var detail: String
    var status: String
}

struct TodayStatus: Hashable {
    var date: String
    var total: Int
    var completed: Int
    var pending: Int
    var items: [TodayMedicationItem]
}

struct TodayMedicationItem: Identifiable, Hashable {
    var id: Int { reminderBackendID ?? fallbackID }
    var fallbackID: Int
    var reminderBackendID: Int?
    var medicineName: String
    var memberName: String
    var time: String
    var mealLabel: String
    var dose: String
    var status: String
    var recordBackendID: Int?
    var takenAt: String?

    var isCompleted: Bool {
        status.contains("已") || recordBackendID != nil
    }
}
