import streamlit as st

st.set_page_config(
    page_title="مصحف كبار القراء",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#0f172a">

    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    .header-title {
        text-align: center;
        color: #38bdf8;
        font-family: 'Cairo', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 5px;
    }
    
    .header-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        border: 2px solid #334155;
        border-radius: 15px;
        width: 100%;
        padding: 20px;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        border-color: #38bdf8;
        color: #38bdf8;
        transform: translateY(-3px);
    }
    
    .player-container {
        background-color: #1e293b;
        border: 2px solid #0284c7;
        padding: 25px;
        border-radius: 20px;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title">🌟 مصحف كبار القراء المصريين 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">اضغط على اسم الشيخ لاختيار السورة والاستماع للتلاوات</div>', unsafe_allow_html=True)
st.markdown("---")

reciters = {
    "الشيخ محمد محمود الطبلاوي": "https://server12.mp3quran.net/tblawi/",
    "الشيخ السيد السعيد": "https://ia800207.us.archive.org/29/items/Quraan-Elsaeed/",
    "الشيخ عبد الباسط عبد الصمد": "https://server7.mp3quran.net/basit/",
    "الشيخ محمد صديق المنشاوي": "https://server10.mp3quran.net/minsh/",
    "الشيخ محمود خليل الحصري": "https://server13.mp3quran.net/husr/",
    "الشيخ مصطفى إسماعيل": "https://server8.mp3quran.net/mustafa/"
}

cols = st.columns(2)

for index, (name, server_url) in enumerate(reciters.items()):
    col = cols[index % 2]
    with col:
        # تم تصحيح الخطأ هنا وإغلاق العلامات بشكل صحيح
        if st.button(name, key=f"btn_{index}"):
            st.session_state.active_reciter = name
            st.session_state.server_url = server_url

if "active_reciter" in st.session_state:
    st.markdown("<div class='player-container'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #38bdf8; text-align: center;'>🎧 اختر سورة من تلاوات: {st.session_state.active_reciter}</h3>", unsafe_allow_html=True)
    
    surah_names = [
        "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
        "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
        "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
        "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
        "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
        "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
        "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
        "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
        "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
        "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
        "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
        "المسد", "الإخلاص", "الفلق", "الناس"
    ]
    
    selected_surah_num = st.selectbox("اختر السورة:", range(1, 115), format_func=lambda x: f"سورة {surah_names[x-1]} (رقم {x})")
    
    formatted_num = str(selected_surah_num).zfill(3)
    audio_link = f"{st.session_state.server_url}{formatted_num}.mp3"
    
    st.markdown(f"<p style='text-align: center; color: #94a3b8;'>جاري تشغيل سورة: {surah_names[selected_surah_num-1]}</p>", unsafe_allow_html=True)
    st.audio(audio_link, format="audio/mp3")
    st.markdown("</div>", unsafe_allow_html=True)
