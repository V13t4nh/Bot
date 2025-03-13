import streamlit as st

def format_number(number, decimals):
    """
    Định dạng số với số chữ số thập phân cố định.
    """
    return f"{number:.{decimals}f}"

def calculate_position_size(entry_price, stop_loss, equity, risk_percentage, contract_size=1):
    """
    Tính kích thước vị thế dựa trên các tham số từ giao diện
    """
    if entry_price == 0 or stop_loss == 0:
        return 0, 0, 0
        
    risk_amount = equity * (risk_percentage / 100)
    
    stop_loss_percentage = abs(entry_price - stop_loss) / entry_price
    
    position_size_units = risk_amount / (entry_price * stop_loss_percentage)
    
    position_size_lots = position_size_units / contract_size
    
    return position_size_lots, position_size_units, risk_amount

STATE_WEIGHTS = {
    "SQTT": 100, "QTT": 75, "XHT": 50, "CTT": 37.5, "T": 25,
    "SQTG": -100, "QTG": -75, "XHG": -50, "CTG": -37.5, "G": -25,
    "SW": 0, "MHT": 12.5, "MHG": -12.5
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

def group_consecutive_frames(frames, states, reference_frames):
    """
    Gộp các khung thời gian liên tiếp có cùng trạng thái.
    
    Args:
        frames: Danh sách các khung thời gian cần gộp
        states: Dictionary ánh xạ từ khung thời gian sang trạng thái
        reference_frames: Danh sách tham chiếu để xác định thứ tự thực tế
    """
    if not frames:
        return []
    
    tf_to_idx = {tf: idx for idx, tf in enumerate(reference_frames)}
    
    sorted_frames = sorted(frames, key=lambda tf: tf_to_idx.get(tf, float('inf')))
    
    result = []
    start = sorted_frames[0]
    current_state = states[start]
    last_idx = tf_to_idx.get(start, -1)
    
    for i in range(1, len(sorted_frames)):
        frame = sorted_frames[i]
        current_idx = tf_to_idx.get(frame, -1)
        
        if states[frame] != current_state or current_idx != last_idx + 1:
            if sorted_frames[i-1] == start:
                result.append(f"{start}: {current_state}")
            else:
                result.append(f"{start}-{sorted_frames[i-1]}: {current_state}")
            start = frame
            current_state = states[frame]
        
        last_idx = current_idx
    
    if sorted_frames[-1] == start:
        result.append(f"{start}: {current_state}")
    else:
        result.append(f"{start}-{sorted_frames[-1]}: {current_state}")
    
    return result

st.markdown("""
    <style>
.stSelectbox > div > div > div {
    width: 100px !important;
    min-width: 100px !important;
}

.stSelectbox [data-baseweb="select"] svg {
    visibility: visible !important;
    display: block !important;
    color: #000 !important;
    opacity: 1 !important;
}

.stSelectbox [data-baseweb="select"] input {
    cursor: pointer !important;
    pointer-events: none !important;
}

.stSelectbox [data-baseweb="select"] {
    border: 1px solid #ced4da !important;
    border-radius: 4px !important;
    background-color: #f8f9fa !important;
}
    table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding: 5px;
        text-align: center;
    }
    
.result-container {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        text-align: center;
    }
    .big-number {
        font-size: 18px;
        font-weight: bold;
    }
    .label {
        font-size: 12px;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Phân Tích Xu Hướng")

st.header("TP & SL")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Công cụ**")
    instrument = st.selectbox(
        "",
        options=["BTC/USD", "ETH/USD", "EUR/USD"], 
        index=0,
        key="instrument"
    )
    
    st.markdown("**Equity ($)**")
    equity = st.number_input("", min_value=100.0, value=100000.0, key="equity", 
                            format="%.1f", step=100.0)
    
    st.markdown("**SL**")
    sl = st.number_input("", value=40000.0, key="sl", 
                         format="%.1f", step=1.0)
    
    st.markdown("**Quy mô hợp đồng (Đơn vị trên Lô)**")
    contract_size = st.number_input("", value=1.0, key="contract_size", 
                                   format="%.1f", step=0.1)

with col2:
    st.markdown("**Loại tiền**")
    currency = st.selectbox(
        "",
        options=["Đô la Mỹ", "Euro"], 
        index=0,
        key="currency"
    )
    
    st.markdown("**Entry**")
    entry = st.number_input("", value=50000.0, key="entry", 
                           format="%.1f", step=1.0)
    
    st.markdown("**TP tham khảo**")
    tp = st.number_input("", value=0.0, key="tp", 
                        format="%.1f", step=1.0)
    
    st.markdown("**Rủi ro**")
    risk_col1, risk_col2 = st.columns([3, 1])
    with risk_col1:
        risk_percentage = st.number_input(
            "",
            value=1.0,
            min_value=0.1,
            max_value=100.0,
            step=0.1,
            format="%.1f",
            key="risk_percentage"
        )
    with risk_col2:
        risk_unit = st.selectbox(
            "",
            options=["%", "$"],
            index=0,
            key="risk_unit"
        )

if risk_unit == "%":
    lots, units, risk_amount = calculate_position_size(
        entry, sl, equity, risk_percentage, contract_size
    )
else:
    risk_amount = risk_percentage
    if entry != 0:
        stop_loss_percentage = abs(entry - sl) / entry
        units = risk_amount / (entry * stop_loss_percentage)
        lots = units / contract_size
    else:
        units = lots = 0

st.markdown('<div class="result-container">', unsafe_allow_html=True)


result_col1, result_col2 = st.columns(2)

with result_col1:
    st.markdown('<p class="label">Các lot (khối lượng giao dịch)</p>', unsafe_allow_html=True)
    if lots < 0.01:
        st.markdown('<p class="big-number">?</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="big-number">{format_number(lots, 2)}</p>', unsafe_allow_html=True)

with result_col2:
    st.markdown('<p class="label">Các đơn vị (khối lượng giao dịch)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="big-number">{format_number(units, 3)}</p>', unsafe_allow_html=True)


st.markdown('<p style="margin-top: 10px;">Rủi ro về tiền</p>', unsafe_allow_html=True)
currency_symbol = "US$" if currency == "Đô la Mỹ" else "€"
st.markdown(f'<p class="big-number">{format_number(risk_amount, 2)} {currency_symbol}</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 

sl_percent = abs(entry - sl) / entry * 100 if entry != 0 else 0
if sl_percent > 1:
    st.warning(f"⚠️ SL cách xa {sl_percent:.2f}%, vượt ngưỡng rủi ro 1%!")

if tp != 0 and entry != 0 and sl != 0:
    profit = abs(tp - entry)
    loss = abs(sl - entry)
    rr_ratio = profit / loss if loss > 0 else 0
    st.write(f"Tỷ lệ R:R = {rr_ratio:.2f}")

st.subheader("Trạng thái")
    
large_timeframes = ["W", "6D", "5D", "4D", "3D", "2D", "D", "H16", "H12"]
states = list(STATE_WEIGHTS.keys())

large_states = {}
for i in range(0, len(large_timeframes), 7):
    rows = st.columns(7)
    for j, col in enumerate(rows):
        if i + j < len(large_timeframes):
            tf = large_timeframes[i + j]
            large_states[tf] = col.selectbox(tf, states, index=states.index("SW"), key=f"large_{tf}")

small_timeframes = ["D", "H16", "H12", "H11", "H10", "H9", "H8", "H7", "H6", "H5", "H4", "H3", "H2", "H1"]

small_states = {}
for i in range(0, len(small_timeframes), 7):
    rows = st.columns(7)
    for j, col in enumerate(rows):
        if i + j < len(small_timeframes):
            tf = small_timeframes[i + j]
            small_states[tf] = col.selectbox(tf, states, index=states.index("SW"), key=f"small_{tf}")

st.header("Xu hướng chung")

p_large = calculate_p(large_timeframes, large_states)
if all(state == "SW" for state in large_states.values()):
    st.warning("⚠️Tất cả khung lớn là Sideway. Vui lòng chọn trạng thái khác để phân tích chính xác hơn.")

increase_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] > 0]
decrease_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] < 0]
sideway_large = [tf for tf in large_timeframes if STATE_WEIGHTS[large_states[tf]] == 0]

increase_large_grouped = group_consecutive_frames(increase_large, large_states, large_timeframes)
decrease_large_grouped = group_consecutive_frames(decrease_large, large_states, large_timeframes)
sideway_large_grouped = group_consecutive_frames(sideway_large, large_states, large_timeframes)

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
    st.warning("⚠️SW cần tín hiệu xác nhận trước khi giao dịch")
st.text_area("Đánh Giá (Xu hướng chung)", max_chars=1000, key="large_assessment", height=200)

st.header("Khung thời gian nhỏ")

p_small = calculate_p(small_timeframes, small_states)
if all(state == "SW" for state in small_states.values()):
    st.warning("⚠️Tất cả khung nhỏ là Sideway. Vui lòng chọn trạng thái khác")

if p_large > 0 and p_small > 0:
    p_small += 10
elif p_large < 0 and p_small < 0: 
    p_small -= 10  
elif p_large > 0 and p_small < 0:
    p_small -= 20
elif p_large < 0 and p_small > 0: 
    st.warning("⚠️Rủi ro tăng 15%: Xu hướng chung giảm nhưng sóng ngắn hạn tăng.")

increase_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] > 0]
decrease_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] < 0]
sideway_small = [tf for tf in small_timeframes if STATE_WEIGHTS[small_states[tf]] == 0]

increase_small_grouped = group_consecutive_frames(increase_small, small_states, small_timeframes)
decrease_small_grouped = group_consecutive_frames(decrease_small, small_states, small_timeframes)
sideway_small_grouped = group_consecutive_frames(sideway_small, small_states, small_timeframes)

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
    st.warning("⚠️Bám vào cấu trúc sóng để vào lệnh, cực kỳ cẩn trọng")
st.text_area("Đánh Giá (Xu hướng nhỏ)", max_chars=1000, key="small_assessment", height=200)

st.header("Nhận định tổng hợp")

# Xác định nếu cả hai đều là Sideway
is_large_sideway = -40 < p_large < 40
is_small_sideway = -40 < p_small < 40

# Xử lý trường hợp đặc biệt khi cả hai đều là Sideway
if is_large_sideway and is_small_sideway:
    st.warning("Cực Kỳ Sideway ↔️, Cực Kỳ Cẩn Trọng")
    st.write(f"Xu hướng chung: {trend_large} ({p_large:.2f}%), Xu hướng nhỏ: {trend_small} ({p_small:.2f}%)")
    st.warning("Cả xu hướng lớn và nhỏ đều không rõ ràng. Hạn chế giao dịch hoặc chỉ tham gia với khối lượng rất nhỏ.")
# So sánh dấu của p_large và p_small để xác định đồng thuận hay ngược pha
elif (p_large > 0 and p_small > 0) or (p_large < 0 and p_small < 0):
    st.write("Đồng Thuận, Kỳ Vọng")
    
    # Hiển thị thông tin về xu hướng
    st.write(f"Xu hướng chung: {trend_large} ({p_large:.2f}%), Xu hướng nhỏ: {trend_small} ({p_small:.2f}%)")
    
    if p_large > 0 and p_small > 0:
        if abs(p_large) > abs(p_small):
            st.warning("Xu hướng tăng đang chậm lại, có thể cân nhắc chốt lời một phần.")
        else:
            st.warning("Sóng ngắn hạn đang tăng mạnh hơn xu hướng chung, có thể tiếp tục đà tăng.")
    elif p_large < 0 and p_small < 0:
        if abs(p_large) > abs(p_small):
            st.warning("Xu hướng giảm đang chậm lại, có thể chờ tín hiệu đảo chiều.")
        else:
            st.warning("Sóng ngắn hạn đang giảm mạnh hơn xu hướng chung, có thể tiếp tục đà giảm.")
else:
    st.write("Ngược Pha, Cẩn Trọng")
    
    # Hiển thị thông tin về xu hướng
    st.write(f"Xu hướng chung: {trend_large} ({p_large:.2f}%), Xu hướng nhỏ: {trend_small} ({p_small:.2f}%)")
    
    if p_large > 0 and p_small < 0:
        st.warning("Xu hướng chung là tăng, nhưng sóng ngắn hạn đang điều chỉnh. Cần xác nhận tín hiệu đảo chiều trước khi vào lệnh.")
    elif p_large < 0 and p_small > 0:
        st.warning("Xu hướng chung là giảm, nhưng sóng ngắn hạn có dấu hiệu hồi phục. Hãy theo dõi thêm tín hiệu xác nhận.")

st.text_area("Đánh Giá (Nhận định tổng hợp)", max_chars=1000, key="overall_assessment", height=200)


st.header("Vùng giá")
st.text_area("Đánh Giá & Kịch Bản", value="Kịch bản Tăng → khung đảm bảo cấu trúc tăng, khung cho phép tăng là ?\nKịch bản Giảm → khung đảm bảo cấu trúc giảm, khung cho phép giảm là ?\nKịch bản Sideway → điều kiện xác nhận đi ngang?", max_chars=3000, key="region_assessment", height=400)
trendline = st.checkbox("Trendline")
col1, col2, col3 = st.columns(3)

with col1:
    resistance_1 = st.number_input("Vùng kháng cự 1", value=100000.0)
    support_1 = st.number_input("Vùng hỗ trợ 1", value=3400.0)

with col2:
    resistance_2 = st.number_input("Vùng kháng cự 2", value=100000.0)
    support_2 = st.number_input("Vùng hỗ trợ 2", value=100000.0)

with col3:
    resistance_3 = st.number_input("Vùng kháng cự 3", value=100000.0)
    support_3 = st.number_input("Vùng hỗ trợ 3", value=100000.0)

supports = [s for s in [support_1, support_2, support_3] if s != 0 and s != 100000]
resistances = [r for r in [resistance_1, resistance_2, resistance_3] if r != 0 and r != 100000]
p_region = calculate_p_region(entry, supports, resistances, p_large)

p_total = (p_large * 0.6) + (p_small * 0.3) + (p_region * 0.1)

st.write(f"**Tổng: {p_total:.2f}%**")

st.header("Hành động")
action = st.checkbox("Hành Động")
stand_out = st.checkbox("Đứng Ngoài")
if action:
    st.text_area("Lý Do", value="Entry có đúng tại Higher Low hoặc Lower High không?\nCó bị FOMO không?", max_chars=1000, key="action_reason")
elif stand_out:
    st.text_area("Lý Do", value="Cần quan sát kỹ khung nào?\nKhoảng thời gian quan trọng cần theo dõi?", max_chars=1000, key="standout_reason")

st.header("Tư duy giao dịch")
cautious = st.checkbox("Cẩn Trọng (giảm 50% Vol)", value=(trend_large != trend_small))
expectation = st.checkbox("Kỳ Vọng (Không sợ rung cây)", value=(trend_large == trend_small))

st.write(f"**Tổng: {p_total:.2f}%**")

st.header("Đề xuất của thuật toán")
if p_total > 60:
    st.write("Bật công tắc tham lam")
elif p_total < 40:
    st.write("Bật công tắc cẩn trọng")
else:
    st.write("Bật công tắc cẩn trọng và công tắc khoảng thời gian")
