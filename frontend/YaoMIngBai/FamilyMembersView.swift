import SwiftUI

struct FamilyMembersView: View {
    @EnvironmentObject private var app: AppState
    @State private var showAddMemberSheet = false
    @State private var memberToDelete: FamilyMember?
    @State private var showDeleteConfirm = false
    @State private var feedbackMessage = ""

    var showBack: Bool = false

    private var pendingCount: Int {
        app.todayItems.filter { !$0.isCompleted }.count
    }

    private var completedCount: Int {
        app.todayItems.filter(\.isCompleted).count
    }

    var body: some View {
        ScrollPage(title: "家人", subtitle: "家庭协同", showBack: showBack, trailingSystemImage: "person.3.fill") {
            HeroCard {
                Text("家庭成员用药状态")
                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                Text(familySummary)
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: "\(app.members.count)", title: "成员", tint: .ybPrimary)
                    MetricTile(number: "\(completedCount)", title: "今日完成", tint: .ybGreen)
                    MetricTile(number: "\(pendingCount)", title: "待服药", tint: .ybOrange)
                }
            }

            YBCard {
                HStack(spacing: 12) {
                    EmojiCircle(emoji: "➕", size: 46, background: Color.ybSoft)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("添加家庭成员")
                            .font(.system(size: 17, weight: .heavy, design: .rounded))
                        Text("新增后可在药箱和提醒里选择这个成员。")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                    Spacer()
                    Button {
                        feedbackMessage = ""
                        showAddMemberSheet = true
                    } label: {
                        Label("添加", systemImage: "plus")
                            .font(.system(size: 13, weight: .heavy, design: .rounded))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .foregroundStyle(Color.white)
                            .background(Color.ybPrimary)
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }

            if !feedbackMessage.isEmpty {
                Text(feedbackMessage)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            SectionTitle(title: "成员列表", trailing: "共 \(app.members.count) 人")
            ForEach(app.members, id: \.id) { member in
                FamilyMemberRow(
                    member: member,
                    statusText: statusText(for: member.name),
                    statusColor: statusColor(for: member.name)
                ) {
                    openMember(member)
                } onDelete: {
                    memberToDelete = member
                    showDeleteConfirm = true
                }
            }
        }
        .refreshable {
            await app.refreshFromBackend()
        }
        .sheet(isPresented: $showAddMemberSheet) {
            AddFamilyMemberSheet { message in
                feedbackMessage = message
            }
            .environmentObject(app)
        }
        .confirmationDialog("删除家庭成员？", isPresented: $showDeleteConfirm, titleVisibility: .visible) {
            if let member = memberToDelete {
                Button("删除 \(member.name)", role: .destructive) {
                    Task {
                        await app.deleteMember(member)
                        feedbackMessage = "已从前端移除 \(member.name)。如果刷新后又出现，需要后端补充成员删除接口。"
                        memberToDelete = nil
                    }
                }
            }
            Button("取消", role: .cancel) {
                memberToDelete = nil
            }
        } message: {
            Text("只删除成员入口，不会删除已经保存的药品、提醒和服药记录。")
        }
    }

    private func openMember(_ member: FamilyMember) {
        app.pendingReminderMember = member.name
        if member.isChildProfile {
            app.path.append(Route.childFeedingRecord(memberName: member.name))
        } else if member.name == "爷爷" {
            app.path.append(Route.elderStatus)
        } else {
            app.path.append(Route.reminderList)
        }
    }

    private var familySummary: String {
        if app.members.isEmpty { return "还没有家庭成员。" }
        if pendingCount == 0 { return "今天的家庭用药提醒都已完成。" }
        return "今天还有 \(pendingCount) 条提醒待服药，可进入成员或提醒列表查看。"
    }

    private func statusText(for memberName: String) -> String {
        let memberItems = app.todayItems.filter { $0.memberName == memberName }
        if memberItems.isEmpty { return "暂无提醒" }
        return memberItems.contains(where: { !$0.isCompleted }) ? "待服药" : "已完成"
    }

    private func statusColor(for memberName: String) -> Color {
        statusText(for: memberName) == "待服药" ? .ybOrange : .ybPrimary
    }
}


private struct FamilyMemberRow: View {
    var member: FamilyMember
    var statusText: String
    var statusColor: Color
    var onOpen: () -> Void
    var onDelete: () -> Void

    @State private var dragOffset: CGFloat = 0
    @State private var isDeleteVisible = false

    private let deleteWidth: CGFloat = 88
    private let rowHeight: CGFloat = 78

    var body: some View {
        GeometryReader { proxy in
            HStack(spacing: 0) {
                memberContent(width: proxy.size.width)
                deleteButton
            }
            .frame(width: proxy.size.width + deleteWidth, alignment: .leading)
            .offset(x: dragOffset)
            .gesture(deleteRevealGesture)
        }
        .frame(height: rowHeight)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .ybCardShadow()
        .accessibilityElement(children: .combine)
        .accessibilityHint("左划露出删除按钮")
    }

    private func memberContent(width: CGFloat) -> some View {
        Button {
            if isDeleteVisible {
                closeDeleteAction()
            } else {
                onOpen()
            }
        } label: {
            HStack(spacing: 12) {
                EmojiCircle(emoji: member.emoji, size: 48)
                VStack(alignment: .leading, spacing: 4) {
                    Text(member.name)
                        .font(.system(size: 16, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color.ybText)
                        .lineLimit(1)
                    Text(member.role.isEmpty ? "家庭成员" : member.role)
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                        .lineLimit(1)
                }
                Spacer()
                StatusPill(text: statusText, color: statusColor)
            }
            .padding(.horizontal, 14)
            .frame(width: width, height: rowHeight, alignment: .leading)
            .background(Color.white)
        }
        .buttonStyle(.plain)
    }

    private var deleteButton: some View {
        Button(role: .destructive) {
            closeDeleteAction()
            onDelete()
        } label: {
            VStack(spacing: 4) {
                Image(systemName: "trash.fill")
                    .font(.system(size: 17, weight: .heavy))
                Text("删除")
                    .font(.system(size: 12, weight: .heavy, design: .rounded))
            }
            .foregroundStyle(Color.white)
            .frame(width: deleteWidth, height: rowHeight)
            .background(Color.ybRed)
        }
        .buttonStyle(.plain)
    }

    private var deleteRevealGesture: some Gesture {
        DragGesture(minimumDistance: 16)
            .onChanged { value in
                let baseOffset = isDeleteVisible ? -deleteWidth : 0
                let proposedOffset = baseOffset + value.translation.width
                dragOffset = min(0, max(proposedOffset, -deleteWidth))
            }
            .onEnded { value in
                let baseOffset = isDeleteVisible ? -deleteWidth : 0
                let proposedOffset = baseOffset + value.translation.width
                let finalOffset = min(0, max(proposedOffset, -deleteWidth))
                let shouldShow = finalOffset < -deleteWidth * 0.35
                    || value.predictedEndTranslation.width < -deleteWidth * 0.8

                withAnimation(.spring(response: 0.28, dampingFraction: 0.86)) {
                    isDeleteVisible = shouldShow
                    dragOffset = shouldShow ? -deleteWidth : 0
                }
            }
    }

    private func closeDeleteAction() {
        withAnimation(.spring(response: 0.28, dampingFraction: 0.86)) {
            isDeleteVisible = false
            dragOffset = 0
        }
    }
}

struct AddFamilyMemberSheet: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.dismiss) private var dismiss

    var onComplete: (String) -> Void

    @State private var emoji = "🙂"
    @State private var name = ""
    @State private var role = "家庭成员"
    @State private var age = ""
    @State private var weight = ""
    @State private var allergy = ""
    @State private var saveMessage = ""
    @State private var isSaving = false

    private var trimmedName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canSave: Bool {
        !trimmedName.isEmpty && !app.members.contains { $0.name == trimmedName }
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 14) {
                    YBCard {
                        HStack(spacing: 12) {
                            EmojiCircle(emoji: emoji.isEmpty ? "🙂" : emoji, size: 52)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("新增家庭成员")
                                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                                Text("保存后可用于药箱归属、提醒对象和记录筛选。")
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                        }
                    }

                    YBCard {
                        SectionTitle(title: "基础信息", trailing: "必填姓名")
                        FormTextField(title: "头像", placeholder: "例如：🙂 / 👩 / 👴", text: $emoji)
                        FormTextField(title: "姓名", placeholder: "例如：爸爸、奶奶、自己", text: $name)
                        FormTextField(title: "身份备注", placeholder: "例如：照护者、长期用药", text: $role)
                    }

                    YBCard {
                        SectionTitle(title: "用药辅助信息", trailing: "选填")
                        FormTextField(title: "年龄", placeholder: "例如：76 岁", text: $age)
                        FormTextField(title: "体重", placeholder: "例如：68kg", text: $weight)
                        FormTextField(title: "过敏史", placeholder: "例如：无 / 青霉素", text: $allergy)
                    }

                    if !saveMessage.isEmpty {
                        Text(saveMessage)
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    PrimaryButton(title: isSaving ? "保存中..." : "保存成员", systemImage: "checkmark.circle.fill") {
                        Task { await save() }
                    }
                    .disabled(!canSave || isSaving)
                    .opacity(canSave && !isSaving ? 1 : 0.45)
                }
                .padding(18)
            }
            .background(Color.ybScreen.ignoresSafeArea())
            .navigationTitle("添加成员")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
            }
        }
    }

    private func save() async {
        guard canSave else {
            saveMessage = trimmedName.isEmpty ? "请先填写成员姓名。" : "这个成员已经存在。"
            return
        }

        isSaving = true
        defer { isSaving = false }

        let member = FamilyMember(
            emoji: emoji.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "🙂" : emoji,
            name: trimmedName,
            role: role.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "家庭成员" : role,
            status: "",
            age: age,
            weight: weight,
            allergy: allergy
        )

        do {
            _ = try await app.saveMember(member)
            onComplete("已添加家庭成员：\(trimmedName)。")
            dismiss()
        } catch {
            saveMessage = "保存失败，请确认后端 /api/members 接口正在运行。"
        }
    }
}
