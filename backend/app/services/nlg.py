MESSAGES = {
    "diabetes.high_sugar": (
        "Sản phẩm {{ name }} có hàm lượng đường cao ({{ sugars }}g/100g). "
        "Với tình trạng tiểu đường, bạn nên hạn chế hoặc tránh sản phẩm này."
    ),
    "diabetes.nova4": (
        "{{ name }} thuộc nhóm thực phẩm siêu chế biến (NOVA 4), "
        "thường chứa nhiều đường và chất béo — không phù hợp với người tiểu đường."
    ),
    "hypertension.high_sodium": (
        "Sản phẩm có hàm lượng natri cao ({{ sodium }}mg/100g). "
        "Người cao huyết áp nên ưu tiên thực phẩm ít muối hơn."
    ),
    "hypertension.high_salt": (
        "Hàm lượng muối {{ salt }}g/100g vượt mức khuyến nghị cho người cao huyết áp."
    ),
    "gout.high_protein": (
        "Protein {{ proteins }}g/100g — người bị gout nên thận trọng với lượng protein cao."
    ),
    "kidney.high_sodium": (
        "Natri {{ sodium }}mg/100g — quá cao cho người bệnh thận. Hãy tham khảo ý kiến bác sĩ."
    ),
    "kidney.high_protein": (
        "Protein {{ proteins }}g/100g — cần kiểm soát khi có bệnh thận."
    ),
    "celiac.gluten": (
        "Thành phần có thể chứa gluten (lúa mì/mì). "
        "Người celiac cần tránh hoàn toàn sản phẩm này."
    ),
    "allergen.match": (
        "Cảnh báo: sản phẩm có thể chứa {{ matched_allergens }} — chất bạn đã khai báo dị ứng."
    ),
    "age.child_sodium": (
        "Natri {{ sodium }}mg/100g cao so với nhu cầu của trẻ. Nên hạn chế."
    ),
    "age.child_nova4": (
        "Thực phẩm siêu chế biến không phù hợp cho trẻ em."
    ),
    "age.newborn_processed": (
        "{{ name }} là thực phẩm chế biến — không phù hợp trẻ sơ sinh. "
        "Trẻ 0-12 tháng chỉ nên dùng sữa mẹ hoặc sữa công thức theo chỉ định bác sĩ."
    ),
    "age.honey": (
        "Sản phẩm có thể chứa mật ong — tuyệt đối không cho trẻ dưới 12 tháng."
    ),
    "age.newborn_sodium": (
        "Natri {{ sodium }}mg/100g vượt mức an toàn cho trẻ sơ sinh."
    ),
    "age.toddler_nova4": (
        "Thực phẩm siêu chế biến không phù hợp trẻ 1-2 tuổi."
    ),
    "age.toddler_sodium": (
        "Natri {{ sodium }}mg/100g cao cho trẻ 1-2 tuổi."
    ),
    "age.preschool_nova4": (
        "Nên hạn chế đồ ăn siêu chế biến, ưu tiên thực phẩm tươi cho trẻ."
    ),
    "age.child_nova4_limit": (
        "{{ name }} là thực phẩm chế biến dành cho trẻ nhỏ. Có thể dùng như món ăn vặt không "
        "thường xuyên, nhưng không nên thay thế trái cây tươi hoặc bữa ăn chính. Nếu trẻ ăn "
        "hằng ngày, nên cân nhắc giảm tần suất."
    ),
    "age.preschool_sugar": (
        "Đường {{ sugars }}g/100g cao cho trẻ 2-4 tuổi."
    ),
    "age.no_instant_noodles": (
        "Mì ăn liền/mì gói không phù hợp trẻ nhỏ — thường chứa nhiều muối và phụ gia."
    ),
    "age.pregnant_additives": (
        "Sản phẩm chứa phụ gia (MSG/nitrite) — phụ nữ mang thai nên thận trọng."
    ),
    "goal.weight_loss_cal": (
        "Năng lượng {{ energy_kcal }}kcal/100g khá cao nếu bạn đang giảm cân."
    ),
    "goal.low_sugar": (
        "Đường {{ sugars }}g/100g vượt mục tiêu hạn chế đường (<5g/100g)."
    ),
    "goal.low_sodium": (
        "Natri {{ sodium }}mg/100g vượt mục tiêu ăn ít muối (<300mg/100g)."
    ),
    "goal.low_sat_fat": (
        "Chất béo bão hòa {{ saturated_fat }}g/100g cao hơn khuyến nghị."
    ),
    "goal.muscle_low_protein": (
        "Protein chỉ {{ proteins }}g/100g — thấp cho mục tiêu tăng cơ."
    ),
    "general.nova4": (
        "{{ name }} có mức độ chế biến cao (NOVA 4). Phù hợp dùng thỉnh thoảng; nên ưu tiên "
        "thực phẩm tươi, ít chế biến trong bữa ăn hằng ngày. NOVA phản ánh mức độ chế biến, "
        "không phải mức độ an toàn."
    ),
    "general.nutri_score_low": (
        "Nutri-Score {{ nutri_score | upper }} cho thấy giá trị dinh dưỡng chưa tốt."
    ),
    "general.msg": (
        "Sản phẩm chứa MSG (E621). Một số người có thể nhạy cảm với glutamate."
    ),
    "positive.nutri_score": (
        "Nutri-Score {{ nutri_score | upper }} — lựa chọn dinh dưỡng tốt!"
    ),
    "positive.fiber": (
        "Giàu chất xơ ({{ fiber }}g/100g) — tốt cho tiêu hóa."
    ),
    "positive.nova1": (
        "Thực phẩm chưa qua chế biến (NOVA 1) — lựa chọn lành mạnh."
    ),
}

SUMMARY_TEMPLATES = {
    "excellent": "{{ name }} phù hợp tốt với profile sức khỏe của bạn ({{ score }}/100).",
    "good": "{{ name }} khá phù hợp ({{ score }}/100), nhưng hãy lưu ý một số điểm bên dưới.",
    "moderate": "{{ name }} có mức độ phù hợp trung bình ({{ score }}/100). Cân nhắc kỹ trước khi sử dụng thường xuyên.",
    "poor": "{{ name }} không phù hợp với profile của bạn ({{ score }}/100). Nên tìm sản phẩm thay thế.",
    "danger": "{{ name }} có cảnh báo nghiêm trọng! Không khuyến khích sử dụng với profile hiện tại.",
}

# Câu tóm tắt khi KHÔNG có cảnh báo nào — tránh nhắc tới "điểm bên dưới" gây hiểu nhầm
SUMMARY_TEMPLATES_NO_WARNINGS = {
    "excellent": "{{ name }} phù hợp tốt với profile sức khỏe của bạn ({{ score }}/100).",
    "good": "{{ name }} khá phù hợp với profile sức khỏe của bạn ({{ score }}/100), không phát hiện cảnh báo nào.",
    "moderate": "{{ name }} có mức độ phù hợp trung bình ({{ score }}/100).",
    "poor": "{{ name }} không phù hợp với profile của bạn ({{ score }}/100). Nên tìm sản phẩm thay thế.",
    "danger": "{{ name }} có cảnh báo nghiêm trọng! Không khuyến khích sử dụng với profile hiện tại.",
}

POSITIVE_MESSAGES = {
    "positive.nutri_score": "Nutri-Score {{ nutri_score | upper }} — dinh dưỡng tốt",
    "positive.fiber": "Giàu chất xơ ({{ fiber }}g/100g)",
    "positive.nova1": "Thực phẩm ít chế biến (NOVA 1)",
}
