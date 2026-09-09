import SwiftUI
import PhotosUI
import Foundation

struct AddMedicineView: View {
    @EnvironmentObject private var app: AppState
    @State private var searchText = ""
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var selectedImage: UIImage?
    @State private var showCamera = false
    @State private var isRecognizing = false
    @State private var message = "对准药品名称、用法用量、禁忌和注意事项。识别后先查看信息，需要时再加入家庭药箱。"

    var showBack: Bool = false

    private var trimmedSearchText: String {
        searchText.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var searchResults: [Medicine] {
        guard !trimmedSearchText.isEmpty else { return [] }

        return app.medicines.filter { medicine in
            medicine.name.localizedCaseInsensitiveContains(trimmedSearchText)
                || medicine.category.localizedCaseInsensitiveContains(trimmedSearchText)
                || medicine.owner.localizedCaseInsensitiveContains(trimmedSearchText)
        }
    }

    var body: some View {
        ScrollPage(
            title: "识别或查询药品",
            subtitle: "查看结果后，可自行选择是否加入家庭药箱",
            showBack: showBack,
            trailingSystemImage: "questionmark.circle"
        ) {
            YBCard {
                VStack(spacing: 12) {
                    if let selectedImage {
                        Image(uiImage: selectedImage)
                            .resizable()
                            .scaledToFill()
                            .frame(height: 180)
                            .clipped()
                            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                    } else {
                        VStack(spacing: 12) {
                            EmojiCircle(emoji: "📷", size: 64, background: Color.ybSoft)
                            Text("拍摄药盒 / 说明书")
                                .font(.system(size: 20, weight: .heavy, design: .rounded))
                            Text(message)
                                .font(.ybBody)
                                .foregroundStyle(Color.ybMuted)
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                    }

                    HStack(spacing: 10) {
                        PhotosPicker(selection: $selectedPhoto, matching: .images) {
                            Label("相册选择", systemImage: "photo")
                                .font(.system(size: 14, weight: .heavy, design: .rounded))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 13)
                                .foregroundStyle(Color.ybPrimary)
                                .background(Color.ybSoft)
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }

                        Button {
                            showCamera = true
                        } label: {
                            Label("打开相机", systemImage: "camera.fill")
                                .font(.system(size: 14, weight: .heavy, design: .rounded))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 13)
                                .foregroundStyle(Color.white)
                                .background(Color.ybPrimary)
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }
                    }

                    if selectedImage != nil {
                        PrimaryButton(title: isRecognizing ? "识别中..." : "识别并查看用药卡片", systemImage: "text.viewfinder") {
                            Task { await runOCR() }
                        }
                        .disabled(isRecognizing)
                    }
                }
            }

            YBCard {
                Text("输入药名查询")
                    .font(.ybCardTitle)

                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(Color.ybMuted)
                    TextField("例如：布洛芬、降压药", text: $searchText)
                        .font(.ybBody)
                        .submitLabel(.search)
                        .onSubmit {
                            openFirstSearchResult()
                        }
                    if let firstResult = searchResults.first {
                        Button("查看") {
                            openMedicine(firstResult)
                        }
                        .font(.system(size: 13, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color.ybPrimary)
                    }
                }
                .padding(14)
                .background(Color.ybScreen)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

                if !trimmedSearchText.isEmpty {
                    if searchResults.isEmpty {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("家庭药箱中暂时没有找到“\(trimmedSearchText)”。可以把药名发给解析接口，先生成一张待核对用药卡片。")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                            SecondaryButton(title: "按药名查询说明", systemImage: "magnifyingglass") {
                                Task { await searchByName() }
                            }
                        }
                    } else {
                        ForEach(Array(searchResults.prefix(5))) { medicine in
                            Button {
                                openMedicine(medicine)
                            } label: {
                                HStack(spacing: 12) {
                                    EmojiCircle(emoji: medicine.emoji, size: 42)
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(medicine.name)
                                            .font(.system(size: 15, weight: .heavy, design: .rounded))
                                            .foregroundStyle(Color.ybText)
                                        Text("\(medicine.spec) · \(medicine.category)")
                                            .font(.ybCaption)
                                            .foregroundStyle(Color.ybMuted)
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .font(.system(size: 12, weight: .heavy))
                                        .foregroundStyle(Color.ybMuted)
                                }
                                .padding(.vertical, 4)
                            }
                            .buttonStyle(.plain)
                            Divider()
                        }
                    }
                }
            }


            YBCard {
                HStack(alignment: .top, spacing: 12) {
                    EmojiCircle(emoji: "🛡️", size: 42, background: Color.ybSoft)
                    VStack(alignment: .leading, spacing: 5) {
                        Text("安全边界")
                            .font(.system(size: 15, weight: .heavy, design: .rounded))
                        Text("本 App 只整理说明书信息与提醒计划，不提供诊断、处方或药品推荐。")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                }
            }
        }
        .sheet(isPresented: $showCamera) {
            CameraPicker(image: $selectedImage)
                .ignoresSafeArea()
        }
        .onChange(of: selectedPhoto) { newItem in
            Task {
                guard let newItem else { return }
                if let data = try? await newItem.loadTransferable(type: Data.self),
                   let uiImage = UIImage(data: data) {
                    await MainActor.run {
                        selectedImage = uiImage
                        message = "图片已选择。请点击识别按钮，识别后会先进入待核对卡片。"
                    }
                }
            }
        }
    }

    private func openFirstSearchResult() {
        if let medicine = searchResults.first {
            openMedicine(medicine)
        } else {
            Task { await searchByName() }
        }
    }

    
    private func searchByName() async {
    guard !trimmedSearchText.isEmpty else {
        return
    }

    isRecognizing = true

    defer {
        isRecognizing = false
    }

    do {
        let medicine = try await BackendClient.shared
            .parseInstructionText(
                trimmedSearchText
            )

        app.lastOCRText = trimmedSearchText
        app.currentMedicine = medicine
        app.path.append(Route.medicineCard)
    } catch {
        message = "无法连接说明书解析服务，请检查后端和网络后重试。"
    }
}
    
    
    

    private func openMedicine(_ medicine: Medicine) {
        app.currentMedicine = medicine
        app.path.append(medicine.backendID == nil ? Route.medicineCard : Route.medicineDetail)
    }

    
    private func runOCR() async {
    guard let selectedImage else {
        return
    }

    isRecognizing = true

    defer {
        isRecognizing = false
    }

    do {
        let text = try await OCRService.shared
            .recognizeText(
                from: selectedImage
            )

        print("\n==============================")
        print("Vision OCR 原始识别结果：")
        print(text)
        print("Vision OCR 原始识别结果结束")
        print("==============================\n")

        let finalText = text.trimmingCharacters(
            in: .whitespacesAndNewlines
        )

        guard !finalText.isEmpty else {
            message =
                "没有识别到清晰文字，请重新拍摄。"
            return
        }

        let medicine = try await BackendClient.shared
            .parseInstructionText(finalText)

        app.lastOCRText = finalText
        app.currentMedicine = medicine

        switch medicine.parseQuality {
        case "good":
            message = "识别完成，请核对用药信息。"

        case "partial":
            message =
                "部分信息未识别，请在保存前补充修改。"

        case "poor":
            message =
                "识别信息较少，请重新拍摄或手动填写。"

        default:
            message = "识别完成，请核对用药信息。"
        }

        app.path.append(Route.medicineCard)
    } catch {
        message =
            "OCR 已完成，但无法连接后端解析服务，请检查网络和后端地址。"
    }
}
    
    
}
