import streamlit as st


STATE_WEIGHTS = {
    "SQTT": 100, "QTT": 75, "XHT": 50, "CTT": 37.5, "T": 25,
    "SQTG": -100, "QTG": -75, "XHG": -50, "CTG": -37.5, "G": -25,
    "SW": 0, "A": 12.5, "B": -12.5
}


def calculate_p(timeframes, selected_states):
    total_weight = sum(STATE_WEIGHTS[selected_states[tf]] for tf in timeframes)
    num_frames = len(timeframes)
    return total_weight / num_frames if num_frames > 0 else 0

def calculate_p_region(price_entry, supports, resistances, p_large):
    min_distance = float('inf')
    nearest_level = None
    for level in supports + resistances:
        if abs(price_entry - level) < min_distance and level != 0 and level != 100000:
            min_distance = abs(price_entry - level)
            nearest_level = level
    
    if nearest_level in supports:
        if price_entry > nearest_level:  
            if p_large > 0:
                return 5
            elif p_large < 0:
                return -5
            else:
                return 2
        else:  
            return 0
    elif nearest_level in resistances:
        if price_entry < nearest_level: 
            if p_large > 0:
                return -5
            elif p_large < 0:
                return 5
            else:
                return -2
        else:  
            return 0
    return 0

def classify_trend(p):
    if p >= 60:
        return "Tăng mạnh"
    elif 40 <= p < 60:
        return "Tăng vừa"
    elif -40 < p < 40:
        return "Sideway"
    elif -60 < p <= -40:
        return "Giảm vừa"
    else:
        return "Giảm mạnh"

def group_consecutive_frames(frames, states):
    if not frames:
        return []
    result = []
    start = frames[0]
    current_state = states[start]
    for i in range(1, len(frames)):
        if states[frames[i]] != current_state:
            if frames[i-1] == start:
                result.append(f"{start}: {current_state}")
            else:
                result.append(f"{start}-{frames[i-1]}: {current_state}")
            start = frames[i]
            current_state = states[start]
    if frames[-1] == start:
        result.append(f"{start}: {current_state}")
    else:
        result.append(f"{start}-{frames[-1]}: {current_state}")
    return result

st.markdown("""
    <style>
    .stSelectbox > div > div > div {
        width: 100px !important;  /* Độ rộng vừa đủ cho 10 ký tự */
        min-width: 100px !important;
    }
    table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding: 5px;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Bot Test")

st.header("TP & SL")
equity = st.number_input("Equity ($)", min_value=100.0, value=100000.0)
entry = st.number_input("Entry", value=3420.0)
sl = st.number_input("SL", value=3380.0)
tp = st.number_input("TP tham khảo", value=0.0)

risk_amount = equity * 0.01
sl_percent = abs(entry - sl) / entry * 100 if entry != 0 else 0
position_size = risk_amount / (sl_percent / 100 * equity) if sl_percent > 0 else 0
st.write(f"Khối lượng đề xuất: {position_size:.2f} lot")
if sl_percent > 5:
    st.warning("Vượt ngưỡng rủi ro 5%!")

st.header("1. Xu hướng chung")
large_timeframes = ["H12", "H16", "1D", "2D", "3D", "4D", "5D", "6D", "W"]
states = list(STATE_WEIGHTS.keys())

st.subheader("Chọn trạng thái cho khung lớn")
large_states = {}
for i in range(0, len(large_timeframes), 7):
    rows = st.columns(7)
    for j, col in enumerate(rows):
        if i + j < len(large_timeframes):
            tf = large_timeframes[i + j]
            large_states[tf] = col.selectbox(tf, states, index=states.index("SW"), key=f"large_{tf}")

p_large = calculate_p(large_timeframes, large_states)
if all(state == "SW" for state in large_states.values()):
    st.warning("Tất cả khung lớn là Sideway. Vui lòng chọn trạng thái khác để phân tích chính xác hơn.")

increase_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] > 0]
decrease_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] < 0]
sideway_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] == 0]

increase_large_grouped = group_consecutive_frames(increase_large, large_states)
decrease_large_grouped = group_consecutive_frames(decrease_large, large_states)
sideway_large_grouped = group_consecutive_frames(sideway_large, large_states)

st.subheader("Bảng phân loại xu hướng chung")
table_html = """
<table style="width:100%">
    <tr>
        <th>Tăng</th>
        <th>Giảm</th>
    </tr>
    <tr>
        <td>{}</td>
        <td>{}</td>
    </tr>
    <tr>
        <td colspan="2">Sideway: {}</td>
    </tr>
</table>
""".format(
    "<br>".join(increase_large_grouped) if increase_large_grouped else "Không có",
    "<br>".join(decrease_large_grouped) if decrease_large_grouped else "Không có",
    " | ".join(sideway_large_grouped) if sideway_large_grouped else "Không có"
)
st.markdown(table_html, unsafe_allow_html=True)

trend_large = classify_trend(p_large)
st.write(f"**Kết luận xu hướng chung**: {trend_large} ({p_large:.2f}%)")
if trend_large == "Sideway":
    st.warning("SW! Cần tín hiệu xác nhận trước khi giao dịch")
st.text_area("Đánh Giá (Xu hướng chung)", max_chars=1000, key="large_assessment")

st.header("2. Khung thời gian nhỏ")
small_timeframes = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10", "H11", "H12", "H16", "1D"]

st.subheader("Chọn trạng thái cho khung nhỏ")
small_states = {}
for i in range(0, len(small_timeframes), 7):
    rows = st.columns(7)
    for j, col in enumerate(rows):
        if i + j < len(small_timeframes):
            tf = small_timeframes[i + j]
            small_states[tf] = col.selectbox(tf, states, index=states.index("SW"), key=f"small_{tf}")

# Tính P nhỏ
p_small = calculate_p(small_timeframes, small_states)
if all(state == "SW" for state in small_states.values()):
    st.warning("Tất cả khung nhỏ là Sideway. Vui lòng chọn trạng thái khác để phân tích chính xác hơn.")

if p_large > 0 and p_small > 0:  
    p_small += 10
elif p_large < 0 and p_small < 0:  
    p_small -= 10  
elif p_large > 0 and p_small < 0: 
    p_small -= 20
elif p_large < 0 and p_small > 0:  
    st.warning("Rủi ro tăng 15%: Xu hướng chung giảm nhưng sóng ngắn hạn tăng.")

increase_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] > 0]
decrease_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] < 0]
sideway_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] == 0]

increase_small_grouped = group_consecutive_frames(increase_small, small_states)
decrease_small_grouped = group_consecutive_frames(decrease_small, small_states)
sideway_small_grouped = group_consecutive_frames(sideway_small, small_states)

st.subheader("Bảng phân loại xu hướng nhỏ")
table_html = """
<table style="width:100%">
    <tr>
        <th>Tăng</th>
        <th>Giảm</th>
    </tr>
    <tr>
        <td>{}</td>
        <td>{}</td>
    </tr>
    <tr>
        <td colspan="2">Sideway: {}</td>
    </tr>
</table>
""".format(
    "<br>".join(increase_small_grouped) if increase_small_grouped else "Không có",
    "<br>".join(decrease_small_grouped) if decrease_small_grouped else "Không có",
    " | ".join(sideway_small_grouped) if sideway_small_grouped else "Không có"
)
st.markdown(table_html, unsafe_allow_html=True)

trend_small = classify_trend(p_small)
st.write(f"**Kết luận xu hướng nhỏ**: {trend_small} ({p_small:.2f}%)")
if trend_small == "Sideway":
    st.warning("SW! Bám vào cấu trúc sóng để vào lệnh, cực kỳ cẩn trọng")
st.text_area("Đánh Giá (Xu hướng nhỏ)", max_chars=1000, key="small_assessment")

st.header("3. Nhận định tổng hợp")
if trend_large == trend_small:
    st.write("Đồng Thuận, Kỳ Vọng")
else:
    st.write(f"Xu hướng chung: {trend_large}, Xu hướng nhỏ: {trend_small}")
    if "Tăng" in trend_large and "Giảm" in trend_small:
        st.write("Xu hướng chung là Tăng, nhưng sóng ngắn hạn đang điều chỉnh. Cần xác nhận tín hiệu đảo chiều trước khi vào lệnh.")
    elif "Giảm" in trend_large and "Tăng" in trend_small:
        st.write("Xu hướng chung là Giảm, nhưng sóng ngắn hạn có dấu hiệu hồi phục. Hãy theo dõi thêm tín hiệu xác nhận.")
    st.write("Ngược Pha, Cẩn Trọng")
st.text_area("Đánh Giá (Nhận định tổng hợp)", max_chars=1000, key="summary_assessment")

# 4. Vùng giá
st.header("4. Vùng giá")
st.text_area("Đánh Giá & Kịch Bản", value="Kịch bản Tăng → khung đảm bảo cấu trúc tăng, khung cho phép tăng là ?\nKịch bản Giảm → khung đảm bảo cấu trúc giảm, khung cho phép giảm là ?\nKịch bản Sideway → điều kiện xác nhận đi ngang?", max_chars=3000, key="region_assessment")
trendline = st.checkbox("Trendline")
resistance_1 = st.number_input("Vùng kháng cự 1", value=100000.0)
resistance_2 = st.number_input("Vùng kháng cự 2", value=100000.0)
resistance_3 = st.number_input("Vùng kháng cự 3", value=100000.0)
support_1 = st.number_input("Vùng hỗ trợ 1", value=3400.0)
support_2 = st.number_input("Vùng hỗ trợ 2", value=100000.0)
support_3 = st.number_input("Vùng hỗ trợ 3", value=100000.0)

supports = [s for s in [support_1, support_2, support_3] if s != 0 and s != 100000]
resistances = [r for r in [resistance_1, resistance_2, resistance_3] if r != 0 and r != 100000]
p_region = calculate_p_region(entry, supports, resistances, p_large)

p_total = (p_large * 0.6) + (p_small * 0.3) + (p_region * 0.1)

st.write(f"**Tổng: {p_total:.2f}%**")

st.header("5. Hành động")
action = st.checkbox("Hành Động")
stand_out = st.checkbox("Đứng Ngoài")
if action:
    st.text_area("Lý Do", value="Entry có đúng tại Higher Low hoặc Lower High không?\nCó bị FOMO không?", max_chars=1000, key="action_reason")
elif stand_out:
    st.text_area("Lý Do", value="Cần quan sát kỹ khung nào?\nKhoảng thời gian quan trọng cần theo dõi?", max_chars=1000, key="standout_reason")

st.header("7. Tư duy giao dịch")
cautious = st.checkbox("Cẩn Trọng (giảm 50% Vol)", value=(trend_large != trend_small))
expectation = st.checkbox("Kỳ Vọng (Không sợ rung cây)", value=(trend_large == trend_small))


st.write(f"**Tổng: {p_total:.2f}%**")

st.header("8. Đề xuất của thuật toán")
if p_total > 60:
    st.write("Bật công tắc tham lam")
elif p_total < 40:
    st.write("Bật công tắc cẩn trọng")
else:
    st.write("Bật công tắc cẩn trọng và công tắc khoảng thời gian")