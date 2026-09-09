import SwiftUI

struct MedicineCardView: View {
    @EnvironmentObject private var app: AppState
    @State private var showSaveSheet = false

    var medicine: Medicine { app.currentMedicine }

    var body: some View {
        ScrollPage(title: "用药卡片", subtitle: "识别 / 查询结果", showBack: true, trailingSystemImage: "pencil") {
            YBCard {
                HStack(alignment: .top, spacing: 12) {
                    EmojiCircle(emoji: "⚠️", size: 42, background: Color.ybOrange.opacity(0.12))
                    VStack(alignment: .leading, spacing: 4) {
                        Text("用药安全提示")
                            .font(.system(size: 16, weight: .heavy, design: .rounded))
                        Text("本 App 仅整理说明书信息与提醒计划。保存前请核对包装、说明书或医生药师建议。")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                }
            }

            if medicine.usedSampleFallback || medicine.demoOnly {
                YBCard {
                    HStack(alignment: .top, spacing: 12) {
                        EmojiCircle(emoji: "⚠️", size: 42, background: Color.ybOrange.opacity(0.12))
                        VStack(alignment: .leading, spacing: 4) {
                            Text("⚠️ 部分信息来自演示兜底数据，请核对药品包装和原说明书。")
                                .font(.system(size: 16, weight: .heavy, design: .rounded))
                                .foregroundStyle(Color.ybText)
                            if !medicine.fallbackFields.isEmpty {
                                Text("请重点核对：\(medicine.fallbackFields.joined(separator: "、"))")
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                        }
                    }
                }
            }

            if medicine.needsConfirmation && !(medicine.usedSampleFallback || medicine.demoOnly) {
                YBCard {
                    HStack(alignment: .top, spacing: 12) {
                        EmojiCircle(emoji: "✍️", size: 42, background: Color.ybSoft)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("保存前请核对信息")
                                .font(.system(size: 16, weight: .heavy, design: .rounded))
                            Text(medicine.fallbackFields.isEmpty ? "识别结果需要你确认后才能加入家庭药箱。" : "请重点核对：\(medicine.fallbackFields.joined(separator: "、"))")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                        }
                    }
                }
            }

            YBCard {
                HStack(spacing: 12) {
                    EmojiCircle(emoji: medicine.emoji, size: 52)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(medicine.name)
                            .font(.system(size: 22, weight: .heavy, design: .rounded))
                    }
                    Spacer()
                }

                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 2), spacing: 10) {
                    InfoMini(title: "一次用量", value: emptyText(medicine.dose))
                    InfoMini(title: "每日次数", value: emptyText(medicine.frequency))
                    InfoMini(title: "有效期", value: emptyText(medicine.expiryDisplayText))
                    InfoMini(title: "服用方式", value: emptyText(medicine.method))
                }

                if !medicine.location.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    InfoRow(label: "说明书贮藏提示", value: medicine.location)
                }
            }

            YBCard {
                SectionTitle(title: "风险与特殊人群提示")
                if medicine.risks.isEmpty {
                    Text("未识别到明显风险关键词，但仍需要核对正式说明书。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    TagWrapView(tags: medicine.risks, tint: .ybOrange)
                }
            }

            if !medicine.contraindications.isEmpty {
                YBCard {
                    SectionTitle(title: "禁忌", trailing: "请认真核对")
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(medicine.contraindications, id: \.self) { item in
                            Text("• \(item)")
                                .font(.ybBody)
                                .foregroundStyle(Color.ybText)
                        }
                    }
                }
            }

            if !medicine.precautions.isEmpty {
                YBCard {
                    SectionTitle(title: "注意事项", trailing: "请认真核对")
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(medicine.precautions, id: \.self) { item in
                            Text("• \(item)")
                                .font(.ybBody)
                                .foregroundStyle(Color.ybText)
                        }
                    }
                }
            }

            YBCard {
                SectionTitle(title: "补充说明", trailing: "保存前可修改")
                Text(emptyText(medicine.note))
                    .font(.ybBody)
                    .lineSpacing(4)
                    .foregroundStyle(Color.ybText)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 2), spacing: 10) {
                SecondaryButton(title: "语音播报", systemImage: "speaker.wave.2.fill") {
                    app.speakCurrentMedicine()
                }
                SecondaryButton(title: "保存后设提醒", systemImage: "alarm.fill") {
                    showSaveSheet = true
                }
                PrimaryButton(title: "核对后加入药箱", systemImage: "plus.circle.fill") {
                    showSaveSheet = true
                }
                SecondaryButton(title: "完整说明", systemImage: "doc.text.fill") {
                    app.path.append(Route.medicineDetail)
                }
            }
        }
        .sheet(isPresented: $showSaveSheet) {
            MedicineSaveSheet(medicine: medicine)
                .environmentObject(app)
        }
    }

    private func emptyText(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "未填写" : value
    }
}

enum MedicineSaveMode: Equatable {
    case add
    case edit

    var title: String {
        switch self {
        case .add: return "加入家庭药箱"
        case .edit: return "编辑药箱信息"
        }
    }

    var headerSubtitle: String {
        switch self {
        case .add: return "保存前请选择服药成员和家中存放位置"
        case .edit: return "可修改使用者、位置、库存、有效期和状态"
        }
    }

    var primaryButtonTitle: String {
        switch self {
        case .add: return "确认加入家庭药箱"
        case .edit: return "保存药箱信息"
        }
    }

    var successMessage: String {
        switch self {
        case .add: return "已加入家庭药箱。"
        case .edit: return "已保存药箱信息。"
        }
    }
}

struct MedicineSaveSheet: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.dismiss) private var dismiss

    let medicine: Medicine
    let mode: MedicineSaveMode

    @State private var owner: String
    @State private var category: String
    @State private var selectedLocation: String
    @State private var customLocation: String
    @State private var stock: String
    @State private var expiryMode: String
    @State private var productionDate: Date
    @State private var hasProductionDate: Bool
    @State private var shelfLife: String
    @State private var expiryDate: Date
    @State private var hasExpiryDate: Bool
    @State private var dose: String
    @State private var frequency: String
    @State private var mealTime: String
    @State private var method: String
    @State private var note: String
    @State private var status: String
    @State private var isSaving = false
    @State private var saveMessage = ""

    private static let locationOptions = ["客厅药箱", "卧室床头柜", "厨房药箱", "书房抽屉", "随身药包", "其他"]
    private static let statusOptions = ["正常", "需确认", "即将过期", "库存不足"]
    private static let defaultCategories = ["常备药", "长期用药", "退热药", "外用药", "其他"]
    private static let expiryModes = ["包装标注到期日", "保质期（可选生产日期）"]

    init(medicine: Medicine, mode: MedicineSaveMode = .add) {
        self.medicine = medicine
        self.mode = mode
        let trimmedLocation = medicine.location.trimmingCharacters(in: .whitespacesAndNewlines)
        let savedLocationIsPreset = Self.locationOptions.contains(trimmedLocation)
        _owner = State(initialValue: medicine.owner)
        _category = State(initialValue: medicine.category.isEmpty ? "常备药" : medicine.category)
        _selectedLocation = State(initialValue: mode == .edit ? (savedLocationIsPreset ? trimmedLocation : (trimmedLocation.isEmpty ? "" : "其他")) : "")
        _customLocation = State(initialValue: mode == .edit && !savedLocationIsPreset ? trimmedLocation : "")
        _stock = State(initialValue: medicine.stock)
        let rawExpiry = medicine.expiry.trimmingCharacters(in: .whitespacesAndNewlines)
        let recognizedShelfLife = medicine.shelfLife.isEmpty && Self.looksLikeShelfLifeDuration(rawExpiry) ? rawExpiry : medicine.shelfLife
        let parsedProductionDate = Self.parseDate(medicine.productionDate)
        let parsedExpiryDate = Self.parseDate(recognizedShelfLife.isEmpty ? rawExpiry : "")
        _expiryMode = State(initialValue: recognizedShelfLife.isEmpty ? "包装标注到期日" : "保质期（可选生产日期）")
        _productionDate = State(initialValue: parsedProductionDate ?? Date())
        _hasProductionDate = State(initialValue: parsedProductionDate != nil)
        _shelfLife = State(initialValue: recognizedShelfLife)
        _expiryDate = State(initialValue: parsedExpiryDate ?? Date())
        _hasExpiryDate = State(initialValue: parsedExpiryDate != nil)
        _dose = State(initialValue: medicine.dose)
        _frequency = State(initialValue: medicine.frequency)
        _mealTime = State(initialValue: medicine.mealTime)
        _method = State(initialValue: medicine.method)
        _note = State(initialValue: medicine.note)
        _status = State(initialValue: (medicine.status.isEmpty || medicine.status == "待确认" || medicine.status == "待核对") ? "需确认" : medicine.status)
    }

    private var ownerOptions: [String] {
        let names = app.members
            .map { $0.name.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        let baseNames = names.isEmpty ? ["我", "爷爷", "奶奶", "小宝"] : names
        return (["全部人"] + baseNames + [owner])
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .reduce(into: [String]()) { result, item in
                if !result.contains(item) { result.append(item) }
            }
    }

    private var categoryOptions: [String] {
        Array(Set(Self.defaultCategories + app.medicines.map(\.category).filter { !$0.isEmpty } + [category])).sorted()
    }

    private var finalLocation: String {
        if selectedLocation == "其他" {
            return customLocation.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return selectedLocation
    }

    private var calculatedExpiryDate: Date? {
        guard expiryMode == "保质期（可选生产日期）", hasProductionDate else { return nil }
        return Self.expiryDate(from: productionDate, shelfLife: shelfLife)
    }

    private var finalExpiry: String {
        if expiryMode == "包装标注到期日" {
            return hasExpiryDate ? Self.formatDate(expiryDate) : ""
        }
        guard let calculatedExpiryDate else { return "" }
        return Self.formatDate(calculatedExpiryDate)
    }

    private var dateInformationIsValid: Bool {
        if expiryMode == "包装标注到期日" {
            return hasExpiryDate
        }

        let hasShelfLife = !shelfLife.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        return hasShelfLife && (!hasProductionDate || calculatedExpiryDate != nil)
    }

    private var canSave: Bool {
        !owner.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !finalLocation.isEmpty
            && !medicine.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && dateInformationIsValid
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 14) {
                    YBCard {
                        HStack(spacing: 12) {
                            EmojiCircle(emoji: medicine.emoji, size: 52)
                            VStack(alignment: .leading, spacing: 4) {
                                Text(medicine.name)
                                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                                Text(mode.headerSubtitle)
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                        }
                    }

                    YBCard {
                        SelectionBlock(title: "给谁用", subtitle: "必选", options: ownerOptions, selected: $owner)
                    }

                    YBCard {
                        SelectionBlock(title: "家中放在哪里", subtitle: "必选", options: Self.locationOptions, selected: $selectedLocation)
                        if selectedLocation == "其他" {
                            TextField("输入具体位置，例如：爷爷床头第二个抽屉", text: $customLocation)
                                .textFieldStyle(.roundedBorder)
                                .font(.ybBody)
                        }
                        if !medicine.location.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            Text("说明书贮藏提示：\(medicine.location)")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                        }
                    }

                    YBCard {
                        SelectionBlock(title: "药品分类", subtitle: "可改", options: categoryOptions, selected: $category)
                    }

                    YBCard {
                        SelectionBlock(title: "日期信息", subtitle: "请按包装核对", options: Self.expiryModes, selected: $expiryMode)

                        if expiryMode == "包装标注到期日" {
                            Toggle("包装上已标注明确到期日", isOn: $hasExpiryDate)
                                .font(.ybBody)
                                .tint(.ybPrimary)
                            if hasExpiryDate {
                                DatePicker("到期日期", selection: $expiryDate, displayedComponents: .date)
                                    .datePickerStyle(.compact)
                                    .font(.ybBody)
                            }
                        } else {
                            FormTextField(title: "保质期", placeholder: "例如：36个月 / 2年", text: $shelfLife)
                            Toggle("填写生产日期并计算到期日（可选）", isOn: $hasProductionDate)
                                .font(.ybBody)
                                .tint(.ybPrimary)
                            if hasProductionDate {
                                DatePicker("生产日期", selection: $productionDate, in: ...Date(), displayedComponents: .date)
                                    .datePickerStyle(.compact)
                                    .font(.ybBody)
                            }
                            if let calculatedExpiryDate {
                                InfoRow(label: "预计到期日期", value: Self.formatDate(calculatedExpiryDate))
                            } else if hasProductionDate {
                                Text("请输入可计算的保质期，例如“36个月”“2年”或“90天”。")
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybOrange)
                            } else {
                                InfoRow(label: "当前展示", value: shelfLife.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "请填写保质期" : shelfLife)
                                Text("不填写生产日期时，药箱会直接展示保质期，不计算具体到期日。")
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                        }

                        Text("日期计算仅用于药箱提醒，请以药品包装标注为准。")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }

                    YBCard {
                        SectionTitle(title: "保存信息", trailing: "可修改")
                        FormTextField(title: "库存", placeholder: "例如：16 粒 / 半盒", text: $stock)
                        FormTextField(title: "一次用量", placeholder: "例如：1 片", text: $dose)
                        FormTextField(title: "每日次数", placeholder: "例如：每日 2 次", text: $frequency)
                        FormTextField(title: "服用时间", placeholder: "例如：饭后", text: $mealTime)
                        FormTextField(title: "服用方式", placeholder: "例如：温水送服", text: $method)
                    }

                    YBCard {
                        SelectionBlock(title: "当前状态", subtitle: "用于药箱提醒", options: Self.statusOptions, selected: $status)
                    }

                    YBCard {
                        Text("备注")
                            .font(.ybCardTitle)
                        TextField("补充注意事项", text: $note, axis: .vertical)
                            .lineLimit(3...6)
                            .textFieldStyle(.roundedBorder)
                            .font(.ybBody)
                    }

                    if !saveMessage.isEmpty {
                        Text(saveMessage)
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybPrimary)
                    }

                    PrimaryButton(title: isSaving ? "保存中..." : mode.primaryButtonTitle, systemImage: "checkmark.circle.fill") {
                        Task { await save() }
                    }
                    .disabled(!canSave || isSaving)
                    .opacity(canSave && !isSaving ? 1 : 0.45)
                }
                .padding(18)
            }
            .background(Color.ybScreen.ignoresSafeArea())
            .navigationTitle(mode.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
            }
        }
    }

    private static func parseDate(_ value: String) -> Date? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        for format in ["yyyy-MM-dd", "yyyy-MM", "yyyy/MM/dd", "yyyy.MM.dd"] {
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = .current
            formatter.dateFormat = format
            if let date = formatter.date(from: trimmed) { return date }
        }
        return nil
    }

    private static func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private static func looksLikeShelfLifeDuration(_ value: String) -> Bool {
        value.range(of: #"\d+\s*(天|日|个月|月|年)"#, options: .regularExpression) != nil
            && value.range(of: #"\d{4}[-/.年]\d{1,2}"#, options: .regularExpression) == nil
    }

    private static func expiryDate(from productionDate: Date, shelfLife: String) -> Date? {
        guard let number = Medicine.firstNumber(in: shelfLife), number > 0 else { return nil }
        let amount = Int(number)
        if shelfLife.contains("年") {
            return Calendar.current.date(byAdding: .year, value: amount, to: productionDate)
        }
        if shelfLife.contains("个月") || shelfLife.contains("月") {
            return Calendar.current.date(byAdding: .month, value: amount, to: productionDate)
        }
        if shelfLife.contains("天") || shelfLife.contains("日") {
            return Calendar.current.date(byAdding: .day, value: amount, to: productionDate)
        }
        return nil
    }

    private func save() async {
        guard canSave else {
            saveMessage = dateInformationIsValid ? "请先选择服药成员和家中存放位置。" : "请填写保质期，或核对包装上的到期日期。"
            return
        }
        isSaving = true
        defer { isSaving = false }

        var updated = medicine
        updated.owner = owner
        updated.category = category
        updated.location = finalLocation
        updated.stock = stock
        updated.productionDate = expiryMode == "保质期（可选生产日期）" && hasProductionDate ? Self.formatDate(productionDate) : ""
        updated.shelfLife = expiryMode == "保质期（可选生产日期）" ? shelfLife.trimmingCharacters(in: .whitespacesAndNewlines) : ""
        updated.expiry = finalExpiry
        updated.dose = dose
        updated.frequency = frequency
        updated.mealTime = mealTime
        updated.method = method
        updated.status = status

        let storageHint = mode == .add ? medicine.location.trimmingCharacters(in: .whitespacesAndNewlines) : ""
        if mode == .add && !storageHint.isEmpty && storageHint != finalLocation && !note.contains(storageHint) {
            updated.note = note.isEmpty ? "说明书贮藏提示：\(storageHint)" : "\(note)\n说明书贮藏提示：\(storageHint)"
        } else {
            updated.note = note
        }

        do {
            let saved: Medicine
            switch mode {
            case .add:
                saved = try await app.saveMedicine(updated)
                app.currentMedicine = saved
                saveMessage = mode.successMessage
                dismiss()
                app.switchToTab(.box)
            case .edit:
                saved = try await app.updateMedicine(updated)
                app.currentMedicine = saved
                saveMessage = mode.successMessage
                dismiss()
            }
        } catch {
            saveMessage = "保存失败，请确认后端正在运行。"
        }
    }
}

struct FormTextField: View {
    var title: String
    var placeholder: String
    @Binding var text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.ybCaption)
                .foregroundStyle(Color.ybMuted)
            TextField(placeholder, text: $text)
                .textFieldStyle(.roundedBorder)
                .font(.ybBody)
        }
    }
}
