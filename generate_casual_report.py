from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def gen():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(2.54); sec.right_margin = Cm(2.54)

    st = doc.styles['Normal']
    st.font.name = 'Calibri'; st.font.size = Pt(11)
    st.paragraph_format.line_spacing = 1.15
    st.paragraph_format.space_after = Pt(6)

    def p(txt="", bold=False, size=11, align=WD_ALIGN_PARAGRAPH.LEFT, after=6, before=0, italic=False, color=None):
        para = doc.add_paragraph()
        para.alignment = align
        para.paragraph_format.space_after = Pt(after)
        para.paragraph_format.space_before = Pt(before)
        if txt:
            r = para.add_run(txt)
            r.font.name = 'Calibri'; r.font.size = Pt(size)
            r.bold = bold; r.italic = italic
            if color: r.font.color.rgb = RGBColor(*color)
        return para

    def heading(txt, level=1):
        h = doc.add_heading(txt, level=level)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.color.rgb = RGBColor(0x1B, 0x7A, 0x3E)
        return h

    def table(headers, rows, widths=None):
        t = doc.add_table(rows=1, cols=len(headers), style='Light Grid Accent 1')
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(headers):
            t.rows[0].cells[i].text = h
            for r in t.rows[0].cells[i].paragraphs[0].runs:
                r.font.name = 'Calibri'; r.font.size = Pt(10); r.bold = True
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = str(v)
                for r in cells[i].paragraphs[0].runs:
                    r.font.name = 'Calibri'; r.font.size = Pt(10)
        return t

    # ── Title Page ──
    p("", after=60)
    p("🌿", size=36, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    p("Plant Disease Advisor", bold=True, size=28, align=WD_ALIGN_PARAGRAPH.CENTER, after=8, color=(0x1B, 0x7A, 0x3E))
    p("A Cloud-Deployed Web Service for Leaf Disease Diagnosis", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=4, italic=True, color=(0x6B, 0x77, 0x85))
    p("with CNN-Based Classification & LLM-Generated Explanations", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=36, italic=True, color=(0x6B, 0x77, 0x85))
    p("[Your Name]", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=4)
    p("[USN: 1RVXXXXXXXX]", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=4, color=(0x6B, 0x77, 0x85))
    p("School of Computer Science and Engineering, RV University", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    p("October 2026", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, color=(0x6B, 0x77, 0x85))

    # ── What This Project Is About ──
    doc.add_page_break()
    heading("What This Project Is About")
    p("Farmers lose crops to diseases every year, and most of them don't have quick access to an expert who can look at a leaf and tell them what's wrong. We built a web service that does exactly that — you upload a photo of a sick leaf, and it tells you what the disease is, how confident it is, and gives you a plain-English explanation with symptoms, causes, and prevention tips.")
    p("It's not just a model sitting on someone's laptop. It's a real, live, secured web service running on AWS that anyone with a browser can use.")

    p("Here's what it does in a nutshell:", bold=True, before=8)
    p("• Takes a leaf photo (JPEG or PNG) and classifies it into one of 38 plant diseases across 14 crops")
    p("• If it's not confident enough (below 70%), it says \"I'm not sure\" instead of guessing")
    p("• Generates a farmer-friendly explanation using Google's Gemini AI")
    p("• If Gemini is down, it automatically falls back to a built-in knowledge base (no downtime)")
    p("• Has user accounts, login, and saves your diagnosis history")
    p("• Fully deployed on AWS with HTTPS, monitoring, and the whole deal")

    # ── The Tech Stack ──
    heading("The Tech Stack")
    p("Here's everything we used and why:")
    table(["Component", "What We Used", "Why"], [
        ["AI Model", "MobileNetV2 (TFLite, quantized)", "Small (2.5 MB), fast (20 ms), accurate enough (94.7%)"],
        ["Backend", "Python + FastAPI", "Modern, fast, auto-generates API docs"],
        ["Database", "SQLite + SQLAlchemy", "Simple, no extra server needed, works great for this scale"],
        ["Auth", "bcrypt + JWT tokens", "Industry standard, stateless, secure"],
        ["Explanations", "Google Gemini API + local JSON fallback", "AI-generated text with a safety net"],
        ["Cloud Hosting", "AWS EC2 (Ubuntu)", "Full control, persistent database file"],
        ["Static Files", "AWS S3 + CloudFront", "Fast, HTTPS, global CDN"],
        ["Photo Storage", "AWS S3 (separate bucket)", "Durable, cheap, accessed via IAM role"],
        ["Monitoring", "AWS CloudWatch", "Logs, CPU alerts, free tier"],
        ["Frontend", "Vanilla HTML/CSS/JS (single page)", "No build tools, no dependencies, just works"],
        ["Testing", "pytest (11 tests)", "Covers auth, CRUD, isolation, edge cases"],
    ])

    # ── How It Works ──
    heading("How It Works")
    p("The whole flow from upload to result:", bold=True, before=6)
    p("1. User opens the web app (served from CloudFront/S3 over HTTPS)")
    p("2. Registers an account or logs in → gets a JWT token")
    p("3. Uploads a leaf photo")
    p("4. CloudFront forwards the request to our EC2 backend (strips the /api prefix)")
    p("5. Backend validates the image (must be JPEG/PNG, under 5 MB, actually readable)")
    p("6. TFLite model runs inference → outputs disease class + confidence score")
    p("7. If confidence ≥ 70%: calls Gemini for an explanation (or uses the knowledge base)")
    p("8. If confidence < 70%: returns \"uncertain\" and asks for a clearer photo")
    p("9. Saves the result to the database, uploads the photo to S3")
    p("10. Returns everything as clean JSON to the frontend")

    heading("The Cloud Setup", level=2)
    p("We needed to solve one annoying problem: browsers block HTTPS pages from calling HTTP APIs (mixed content). So we can't just point the frontend at the EC2 server's raw IP.")
    p("Solution: CloudFront sits in front of everything under one HTTPS domain. Static files go to S3, API calls go to EC2. A tiny CloudFront Function strips the /api prefix before forwarding. Problem solved — no CORS issues, no mixed content, one clean URL.")

    table(["AWS Service", "What It Does", "Cloud Model (for the report)"], [
        ["EC2", "Runs FastAPI + model + SQLite", "IaaS (we manage the OS)"],
        ["S3 (web bucket)", "Hosts index.html", "Storage"],
        ["S3 (data bucket)", "Stores uploaded leaf photos", "Storage"],
        ["CloudFront", "HTTPS, CDN, path routing", "Edge/CDN"],
        ["Gemini API", "Generates explanations", "SaaS (external service)"],
        ["CloudWatch", "Logs + CPU alerts", "Managed monitoring"],
        ["IAM Role", "EC2 accesses S3 without storing keys", "Security"],
    ])

    # ── The AI Model ──
    heading("The AI Model")
    p("We used transfer learning with MobileNetV2 (pretrained on ImageNet):", bold=True, before=6)
    p("• Froze all 155 base layers (2.26M parameters — not trained)")
    p("• Added our own head: GlobalAveragePooling → Dropout(0.2) → Dense(38, softmax)")
    p("• Only ~48,700 parameters were actually trained")
    p("• Trained for 6 epochs on Google Colab (T4 GPU), took about 15 minutes")
    p("• Converted to TFLite with int8 quantization → shrunk from 9.4 MB to 2.57 MB")

    p("Training data: PlantVillage dataset", bold=True, before=10)
    p("• 54,305 images, 38 classes, 14 crops")
    p("• 80/20 split → 43,444 training / 10,861 validation")
    p("• Lab photos with clean backgrounds (not field photos — this is a known limitation)")

    # ── Results ──
    heading("Results — How Well Does It Work?")

    heading("Overall Performance", level=2)
    table(["What We Measured", "Result"], [
        ["Accuracy (full precision model)", "95.06%"],
        ["Accuracy (quantized TFLite model)", "94.71%"],
        ["95% Confidence Interval", "94.28% to 95.13%"],
        ["Average inference time (CPU)", "20.5 ms"],
        ["Slowest 5% of inferences", "28.0 ms"],
        ["Macro F1-Score", "0.933"],
    ])

    heading("The Confidence Threshold Trick", level=2)
    p("Instead of always giving an answer, we reject predictions where the model isn't confident enough. Here's how different thresholds perform:")
    table(["Threshold", "% of Images Answered", "Accuracy on Those Images"], [
        ["0.50", "98.0%", "95.7%"],
        ["0.60", "95.5%", "96.8%"],
        ["0.70 ← we use this", "92.9%", "97.6%"],
        ["0.80", "89.9%", "98.5%"],
        ["0.90", "85.2%", "99.2%"],
    ])
    p("At 0.70, we skip about 7% of images but accuracy jumps from 94.7% to 97.6%. That's a great trade-off for a diagnostic tool — it's much better to say \"I'm not sure\" than to give wrong advice.")

    heading("Where It Struggles", level=2)
    p("The hardest classes are all tomato diseases that look similar to the human eye:")
    table(["Disease", "Precision", "Recall", "F1", "Why It's Hard"], [
        ["Tomato Early Blight", "0.878", "0.581", "0.699", "Looks like Septoria and Target Spot"],
        ["Potato Healthy", "1.000", "0.560", "0.718", "Only 25 validation images"],
        ["Tomato Target Spot", "0.662", "0.871", "0.752", "Brown spots similar to other diseases"],
        ["Tomato Spider Mites", "0.945", "0.668", "0.782", "Subtle leaf damage patterns"],
    ])

    # ── The API ──
    heading("The API Endpoints")
    table(["Method", "Endpoint", "Auth?", "What It Does"], [
        ["GET", "/health", "No", "Health check — returns {\"status\": \"ok\"}"],
        ["GET", "/classes", "No", "Lists all 38 disease classes"],
        ["POST", "/auth/register", "No", "Create a new user account"],
        ["POST", "/auth/login", "No", "Get a JWT token"],
        ["GET", "/auth/me", "Yes", "Who am I?"],
        ["POST", "/predict", "Yes", "Upload a leaf photo → get diagnosis"],
        ["GET", "/predictions", "Yes", "List your past diagnoses (paginated)"],
        ["GET", "/predictions/{id}", "Yes", "Get a specific diagnosis"],
        ["PUT", "/predictions/{id}", "Yes", "Add a note or correct the label"],
        ["DELETE", "/predictions/{id}", "Yes", "Delete a diagnosis"],
    ])
    p("Full interactive docs are auto-generated at /docs (Swagger UI).")

    # ── Security ──
    heading("Security — What We Did Right")
    p("• Passwords are hashed with bcrypt (never stored in plain text)")
    p("• JWT tokens expire after 60 minutes")
    p("• Every database query is scoped to the logged-in user")
    p("• If you try to access someone else's record, you get 404 (not 403 — so you can't even tell if it exists)")
    p("• Image uploads are validated: must be JPEG or PNG, must be a real image, max 5 MB")
    p("• No API keys or secrets in the code — everything is in environment variables")
    p("• EC2 accesses S3 through an IAM role, not stored credentials")

    # ── Testing ──
    heading("Testing")
    p("We wrote 11 automated tests that run against a temporary database with the LLM disabled:")
    table(["Test", "What It Checks"], [
        ["test_health", "/health returns 200 OK"],
        ["test_classes_lists_38", "/classes returns exactly 38 items"],
        ["test_register_and_duplicate", "Can register; duplicate username → 409"],
        ["test_register_validation", "Short password → 422 validation error"],
        ["test_login_wrong_password", "Wrong password → 401"],
        ["test_me_requires_valid_token", "No token or bad token → 401"],
        ["test_predict_requires_login", "Upload without auth → 401"],
        ["test_predict_rejects_bad_file", "Non-image file → 400"],
        ["test_predict_and_crud_flow", "Full cycle: predict → view → update note → delete"],
        ["test_user_isolation", "User A can't see User B's records"],
        ["test_pagination", "skip/limit query params work correctly"],
    ])
    p("All 11 passed. ✅", bold=True)

    # ── The Frontend ──
    heading("The Web Client")
    p("We built a clean single-page app in plain HTML/CSS/JS (no React, no build tools, no npm). It has:")
    p("• Login / Register screen with tabs")
    p("• Drag-and-drop image upload with preview")
    p("• Confidence bar with color coding (green/yellow/orange)")
    p("• \"Uncertain\" warning when confidence is low")
    p("• Structured explanation display (Summary, Symptoms, Causes, Prevention)")
    p("• Source badge showing whether the explanation came from Gemini or the knowledge base")
    p("• Sidebar with diagnosis history")
    p("• Settings gear to change the API URL (useful for switching between local and AWS)")
    p("• 482 lines total, zero dependencies")

    # ── The Explanation Engine ──
    heading("The Explanation Engine — LLM + Fallback")
    p("This is probably the most interesting engineering decision in the project.", italic=True, before=6)
    p("When the model predicts a disease, we want to explain it in simple terms. We use Google's Gemini API for this — send it the disease name, ask for JSON with summary/symptoms/causes/prevention.")
    p("But here's the thing: external APIs fail. They rate-limit you, they go down, they change their pricing. Our first LLM provider actually blocked our project entirely (HTTP 403). So we built a two-layer system:")
    p("1. Try Gemini first → if it works, tag the response as source: \"llm\"")
    p("2. If Gemini fails for ANY reason (timeout, rate limit, error, turned off), automatically return the answer from a hand-written knowledge base of 38 diseases → tag as source: \"knowledge_base\"")
    p("3. The user always gets an answer. The frontend shows which source was used.")
    p("You can also completely disable the LLM by setting USE_LLM=false in the .env file. The knowledge base handles everything.")

    # ── Did We Meet Our Goals? ──
    heading("Did We Meet Our Goals?")
    table(["Goal", "Target", "Actual Result", "Verdict"], [
        ["Classification accuracy", "≥ 90%", "94.71% (CI: 94.28–95.13%)", "✅ Met"],
        ["Inference speed", "< 100 ms", "Mean 20.5 ms, p95 28.0 ms", "✅ Met (5x faster)"],
        ["Accuracy on confident predictions", "≥ 95%", "97.6%", "✅ Met"],
        ["All tests pass", "11/11", "11/11", "✅ Met"],
        ["Deployed on AWS with monitoring", "Yes", "EC2 + S3 + CloudFront + CloudWatch", "✅ Met"],
    ])

    # ── Known Limitations ──
    heading("Known Limitations (Being Honest)")
    p("• Only covers 38 diseases from PlantVillage — won't recognize anything else")
    p("• Trained on lab photos with clean backgrounds — field photos with dirt, shadows, and multiple leaves will be harder")
    p("• Some diseased tomato leaves get classified as \"healthy\" (precision issue)")
    p("• Gemini's text can vary between calls — it's not deterministic")
    p("• The demo server has CORS set to allow everything (fine for a demo, not for production)")
    p("• SQLite works for this scale but wouldn't handle 1000 concurrent users")

    # ── What We'd Do Next ──
    heading("What We'd Do Next")
    p("1. RAG (Retrieval-Augmented Generation): Feed real agricultural PDFs into a vector database so Gemini's explanations cite actual sources")
    p("2. Fine-tune the CNN: Unfreeze the top layers of MobileNetV2 to better separate those tricky tomato diseases")
    p("3. Docker + Nginx: Containerize everything and add a proper reverse proxy")
    p("4. Field photos: Collect real photos from farms and retrain")
    p("5. Regional languages: Add Hindi/Kannada translations for the explanations")

    # ── References ──
    heading("References")
    refs = [
        "Hughes & Salathé (2015) — PlantVillage dataset. arXiv:1511.08060",
        "Mohanty, Hughes & Salathé (2016) — Deep learning for plant disease detection. Frontiers in Plant Science, 7, 1419",
        "Sandler et al. (2018) — MobileNetV2. CVPR 2018",
        "Barbedo (2018) — Dataset limitations for plant disease classification. Comp. & Elec. in Agriculture, 153",
        "Chow (1970) — Reject option theory. IEEE Trans. Information Theory",
        "Guo et al. (2017) — Neural network calibration. ICML 2017",
        "Fielding (2000) — REST architectural style. PhD dissertation, UC Irvine",
        "Jones, Bradley & Sakimura (2015) — JSON Web Token. RFC 7519",
        "Mell & Grance (2011) — NIST cloud computing definition. SP 800-145",
        "Vaswani et al. (2017) — Transformers (Attention Is All You Need). NeurIPS 2017",
        "Lewis et al. (2020) — Retrieval-Augmented Generation. NeurIPS 2020",
    ]
    for r in refs:
        p(f"• {r}", size=10)

    # ── Save ──
    paths = [
        "F:/plant-disease-advisor/PlantDiseaseAdvisor_Casual_Report.docx",
        "C:/Users/Lenovo/Downloads/PlantDiseaseAdvisor_Casual_Report.docx",
        "C:/Users/Lenovo/OneDrive/Desktop/PlantDiseaseAdvisor_Casual_Report.docx",
    ]
    for path in paths:
        try:
            doc.save(path)
            print(f"Saved: {path}")
        except Exception as e:
            print(f"Could not save to {path}: {e}")

if __name__ == "__main__":
    gen()
