import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def add_page_number_field(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def generate_rvu_report():
    doc = Document()

    # Section 1: Preliminary Pages (Page numbers i, ii, iii... or no page number on cover/certificate)
    sec_prelim = doc.sections[0]
    sec_prelim.top_margin = Cm(2.54)
    sec_prelim.bottom_margin = Cm(2.54)
    sec_prelim.left_margin = Cm(3.81)    # 3.81 cm
    sec_prelim.right_margin = Cm(2.54)
    sec_prelim.page_width = Cm(21.0)     # A4
    sec_prelim.page_height = Cm(29.7)
    sec_prelim.different_first_page_header_footer = False

    # Base Style
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=12, space_after=6, space_before=0, underline=False):
        para = doc.add_paragraph()
        para.alignment = align
        para.paragraph_format.space_before = Pt(space_before)
        para.paragraph_format.space_after = Pt(space_after)
        para.paragraph_format.line_spacing = 1.5
        if text:
            run = para.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(size)
            run.bold = bold
            run.italic = italic
            run.underline = underline
            run.font.color.rgb = RGBColor(0, 0, 0)
        return para

    def format_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            para = hdr_cells[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.runs[0].font.name = 'Times New Roman'
            para.runs[0].font.size = Pt(10)
            para.runs[0].bold = True
            shading = parse_xml(r'<w:shd {} w:fill="F2F4F3"/>'.format(nsdecls('w')))
            hdr_cells[i]._tc.get_or_add_tcPr().append(shading)
        
        for row_data in data:
            row_cells = table.add_row().cells
            for i, val in enumerate(row_data):
                row_cells[i].text = str(val)
                para = row_cells[i].paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT if i != 0 and not isinstance(val, (int, float)) else WD_ALIGN_PARAGRAPH.CENTER
                if len(para.runs) > 0:
                    para.runs[0].font.name = 'Times New Roman'
                    para.runs[0].font.size = Pt(10)
        
        for row in table.rows:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(r'<w:cantSplit {}/>'.format(nsdecls('w'))))
            for i, cell in enumerate(row.cells):
                cell.width = col_widths[i]
                set_cell_margins(cell, 80, 80, 120, 120)
                tcPr = cell._tc.get_or_add_tcPr()
                borders = parse_xml(
                    r'<w:tcBorders {}><w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:left w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/></w:tcBorders>'.format(nsdecls('w'))
                )
                tcPr.append(borders)

    # =========================================================================
    # 1. COVER PAGE (Exact Template Typography)
    # ==========================================
    p("School of Computer Science and Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=24, space_after=18)
    p("OCTOBER, 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_after=36)

    # TITLE OF THE PROJECT REPORT <Times New Roman, Font 20, Bold, CAPS>
    p("PLANT DISEASE ADVISOR: A CLOUD-DEPLOYED RESTFUL WEB SERVICE FOR CNN-BASED LEAF DISEASE DIAGNOSIS WITH LLM-GENERATED EXPLANATIONS",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=20, space_after=36)

    # Submitted in partial fulfillment... <Times New Roman, Font 14, Italic>
    p("Submitted in partial fulfillment for the award of the degree of", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=12)

    # Name of the degree <Times New Roman, Font 22, Bold>
    p("Bachelor of Technology (Honours) in Computer Science and Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=22, space_after=36)

    # by <Times New Roman, Font 14, Italic>
    p("by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=12)

    # NAME OF THE CANDIDATE / USN: [1RXXXXXXXX] <Times New Roman, Font 16, Bold, CAPS>
    p("[NAME OF THE CANDIDATE]\nUSN: [1RVXXXXXXXX]", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=36)

    # Guided by
    p("Guided by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=8)

    # Guide Name <Times New Roman, Font 16, Bold, CAPS>
    # Designation, SOCSE, RV University <Times New Roman, Font 16, Bold, CAPS>
    p("[GUIDE NAME]\nDESIGNATION, SOCSE, RV UNIVERSITY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=0)

    # =========================================================================
    # 2. CERTIFICATE (Exact Template Text & Structure)
    # ==========================================
    doc.add_page_break()
    p("School of Computer Science and Engineering\nRV University\nRV Vidyaniketan, 8th Mile, Mysore Road, Bengaluru, Karnataka, India - 560059",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=12, space_after=30)

    p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p(
        "This is to certify that the project work titled \"PLANT DISEASE ADVISOR: A CLOUD-DEPLOYED RESTFUL WEB SERVICE "
        "FOR CNN-BASED LEAF DISEASE DIAGNOSIS WITH LLM-GENERATED EXPLANATIONS\" has been carried out by [Name of Candidate], "
        "bearing USN: [1RVXXXXXXXX], a bonafide student of the Bachelor of Technology (Honours) in Computer Science and "
        "Engineering programme at the School of Computer Science and Engineering, RV University, Bengaluru, in partial "
        "fulfillment of the requirements for the award of the degree of Bachelor of Technology (Honours) in Computer Science "
        "and Engineering during the academic year 2026–2027.",
        space_after=48
    )

    t_eval = doc.add_table(rows=3, cols=2)
    format_table(t_eval, [Cm(7.5), Cm(7.5)], ["Name of the Examiner", "Signature of Examiner"], [
        ["1. __________________________________", "1. __________________________________"],
        ["2. __________________________________", "2. __________________________________"]
    ])

    # =========================================================================
    # 3. ABSTRACT (Page i)
    # ==========================================
    doc.add_page_break()
    p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, underline=True, space_before=12, space_after=20)

    p(
        "Plant diseases reduce crop yield, and farmers often lack quick access to expert diagnosis. This project presents "
        "Plant Disease Advisor, a RESTful web service that identifies a leaf disease from a photograph and explains it in plain "
        "language. A MobileNetV2 convolutional neural network, adapted by transfer learning on the PlantVillage dataset "
        "(38 classes, 14 crops), classifies the image and achieves 94.71% accuracy (95% CI 94.28 to 95.13) on 10,861 held-out "
        "validation images. Predictions below a 0.70 confidence threshold are rejected, which raises accuracy on the answered "
        "images to 97.6%. A large language model generates the explanation, with automatic fallback to a curated knowledge base "
        "when the model is unavailable."
    )
    p(
        "The service provides user registration, JWT authentication, per-user storage of predictions in a relational database, "
        "photo storage in Amazon S3, and full CRUD endpoints documented with OpenAPI. It is deployed on AWS using EC2, S3, "
        "CloudFront, IAM, and CloudWatch. The work demonstrates web service design, security, testing, and cloud service "
        "models in a single working system."
    )
    p("Keywords: REST API, transfer learning, MobileNetV2, plant disease, AWS, cloud service models.", bold=True, space_before=18)
    p("i", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=72)

    # =========================================================================
    # 4. ACKNOWLEDGMENT (Page ii)
    # ==========================================
    doc.add_page_break()
    p("ACKNOWLEDGMENT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, underline=True, space_before=12, space_after=20)

    p(
        "It is my pleasure to express with deep sense of gratitude to [Internal Guide Name], [Designation], School of Computer "
        "Science and Engineering, RV University, for their constant guidance, continual encouragement, understanding; more than all, "
        "they taught me patience in my endeavor. My association with them is not confined to academics only, but it is a great "
        "opportunity on my part of work with an intellectual and expert in the field of Computer Science and Cloud Computing."
    )
    p(
        "I would like to express my gratitude to Dr Ram Kumar Kakani, Vice Chancellor RV University, and Dr Shobha G, Dean SoCSE, "
        "RV University, for providing with an environment to work in and for their inspiration during the tenure of the course."
    )
    p(
        "I express my sincere gratitude to [Program Director Name], Program Director, B.Tech (H), School of Computer Science & Engineering, "
        "RV University, for the guidance and support provided throughout my course of study. I also extend my heartfelt thanks to all "
        "the faculty members and staff of the School for their constant encouragement, valuable guidance, and assistance, which contributed "
        "significantly to the successful completion of my studies. Finally, I would like to express my deepest gratitude to my parents "
        "for their unwavering support, encouragement, and belief in me throughout this journey."
    )
    p(
        "It is indeed a pleasure to thank my friends who persuaded and encouraged me to take up and complete this task. At last but "
        "not least, I express my gratitude and appreciation to all those who have helped me directly or indirectly toward the "
        "successful completion of this project."
    )
    p("Place: Bangalore\nDate: [Date]", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, space_before=24, space_after=0)
    p("[Name of the Student]\nUSN: [1RVXXXXXXXX]", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, space_before=0, space_after=0)
    p("ii", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=40)

    # =========================================================================
    # 5. CONTENTS (Exact Structure from User Prompt)
    # ==========================================
    doc.add_page_break()
    p("CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)

    t_contents = doc.add_table(rows=1, cols=2)
    format_table(t_contents, [Cm(13.0), Cm(2.0)], ["Item", "Page"], [
        ["ABSTRACT", "i"],
        ["ACKNOWLEDGMENT", "ii"],
        ["CONTENTS", "iii"],
        ["LIST OF FIGURES", "vi"],
        ["LIST OF TABLES", "vii"],
        ["LIST OF ACRONYMS", "viii"],
        ["CHAPTER 1: INTRODUCTION", "1"],
        ["    1.1 INTRODUCTION", "1"],
        ["    1.2 AIM AND OBJECTIVES", "3"],
        ["    1.3 PROBLEM STATEMENT", "4"],
        ["    1.4 SCOPE OF THE PROJECT", "5"],
        ["    1.5 CHALLENGES", "6"],
        ["CHAPTER 2: BACKGROUND", "10"],
        ["    2.1 LITERATURE SURVEY", "10"],
        ["    2.2 REQUIREMENTS", "15"],
        ["CHAPTER 3: METHODOLOGY", "17"],
        ["    3.1 PROPOSED METHODOLOGY", "17"],
        ["    3.2 DATASETS", "19"],
        ["    3.3 FLOW OF THE MODEL", "20"],
        ["CHAPTER 4: RESULTS", "25"],
        ["    4.1 EXPERIMENTAL SETUP", "25"],
        ["    4.2 RESULT SUMMARY TABLES", "27"],
        ["    4.3 ANALYSIS OF RESULTS", "29"],
        ["    4.4 COMPARISON WITH EXISTING METHODS", "30"],
        ["CHAPTER 5: INFERENCES", "35"],
        ["    5.1 KEY FINDINGS", "35"],
        ["    5.2 INTERPRETATION OF RESULTS", "38"],
        ["    5.3 IMPLICATIONS OF THE STUDY", "39"],
        ["    5.4 FULFILLMENT OF OBJECTIVES", "41"],
        ["CHAPTER 6: CONCLUSION", "43"],
        ["    6.1 RESULTS", "43"],
        ["    6.2 FUTURE WORK", "45"],
        ["    6.3 REFERENCES", "46"],
        ["APPENDIX", "47"]
    ])
    p("iii", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=20)

    # =========================================================================
    # 6. LIST OF FIGURES & TABLES & ACRONYMS
    # ==========================================
    doc.add_page_break()
    p("LIST OF FIGURES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    t_lof = doc.add_table(rows=1, cols=2)
    format_table(t_lof, [Cm(13.0), Cm(2.0)], ["Figure Title", "Page"], [
        ["Figure 3.1: High-Level Cloud-Native System Architecture Diagram", "18"],
        ["Figure 3.2: Synchronous Diagnostic Request Sequence Flow", "19"],
        ["Figure 3.3: MobileNetV2 Architecture and Classification Head", "21"],
        ["Figure 3.4: Dual-Engine Explanation Flow with Automatic Fallback", "22"],
        ["Figure 3.5: Relational Database Entity-Relationship (ER) Diagram", "23"],
        ["Figure 3.6: Machine Learning Processing Pipeline Flowchart", "24"]
    ])
    p("vi", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=72)

    doc.add_page_break()
    p("LIST OF TABLES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    t_lot = doc.add_table(rows=1, cols=2)
    format_table(t_lot, [Cm(13.0), Cm(2.0)], ["Table Title", "Page"], [
        ["Table 2.1: Functional Requirements Specification", "15"],
        ["Table 2.2: Non-Functional Operational Requirements", "16"],
        ["Table 3.1: AWS Cloud Components and NIST Service Models", "24"],
        ["Table 4.1: Classification Results on Held-Out Validation Set", "27"],
        ["Table 4.2: Weakest Classes Evaluation Profile", "28"],
        ["Table 4.3: Effect of the Confidence Threshold on Answered Accuracy", "28"],
        ["Table 4.4: Automated Pytest Suite Test Verification Matrix", "29"],
        ["Table 4.5: Comparison with Published Plant Disease Methods", "31"],
        ["Table 5.1: Statistical Hypothesis Verification of Stated Objectives", "41"]
    ])
    p("vii", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=72)

    doc.add_page_break()
    p("LIST OF ACRONYMS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    t_acro = doc.add_table(rows=1, cols=2)
    format_table(t_acro, [Cm(4.0), Cm(11.0)], ["Acronym", "Full Expansion and Definition"], [
        ["API", "Application Programming Interface"],
        ["AWS", "Amazon Web Services"],
        ["CDN", "Content Delivery Network"],
        ["CI", "Confidence Interval"],
        ["CNN", "Convolutional Neural Network"],
        ["CRUD", "Create, Read, Update, Delete"],
        ["EC2", "Elastic Compute Cloud (IaaS Virtual Compute Instance)"],
        ["F1", "Harmonic Mean of Precision and Recall"],
        ["IaaS", "Infrastructure as a Service"],
        ["JWT", "JSON Web Token (RFC 7519)"],
        ["LLM", "Large Language Model"],
        ["PaaS", "Platform as a Service"],
        ["RAG", "Retrieval-Augmented Generation"],
        ["REST", "Representational State Transfer"],
        ["S3", "Simple Storage Service (Cloud Object Store)"],
        ["SaaS", "Software as a Service"],
        ["SOA", "Service-Oriented Architecture"],
        ["TFLite", "TensorFlow Lite Embedded Neural Runtime"]
    ])
    p("viii", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=60)

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 1", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("INTRODUCTION", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("1.1 INTRODUCTION", bold=True, size=14, space_before=12, space_after=6)
    p(
        "Crop diseases cause significant yield loss, and early identification limits their spread. Expert diagnosis is not "
        "always available to small farmers. Deep learning can classify disease from leaf images, but a trained model has no "
        "value to a farmer until it is packaged as a service people can reach. This project turns an image classifier into a "
        "secure, documented, cloud-hosted web service, and adds an LLM-generated explanation so that the output is understandable "
        "and actionable."
    )

    p("1.2 AIM AND OBJECTIVES", bold=True, size=14, space_before=16, space_after=6)
    p("Aim: to design, implement, and deploy a RESTful web service that diagnoses plant leaf diseases from images and explains them.")
    p("Objectives (each is measured in Chapter 5):", bold=True)
    p("1. Classify leaf images into 38 classes with at least 90% accuracy on held-out data.")
    p("2. Keep model inference time under 100 ms per image on general-purpose CPU hardware.")
    p("3. Reject uncertain predictions so that accuracy on answered images is at least 95%.")
    p("4. Provide authenticated CRUD endpoints with per-user data isolation, verified by automated tests.")
    p("5. Deploy the system on AWS using appropriate cloud service models and monitor it.")

    p("1.3 PROBLEM STATEMENT", bold=True, size=14, space_before=16, space_after=6)
    p(
        "There is no simple, secure, publicly reachable service that returns both a disease diagnosis and an understandable "
        "explanation from a leaf photo, and that reports when it is not sure instead of guessing."
    )

    p("1.4 SCOPE OF THE PROJECT", bold=True, size=14, space_before=16, space_after=6)
    p(
        "In scope: 38 PlantVillage classes (14 crops), a REST API, a web client, a database, cloud deployment, and monitoring. "
        "Out of scope: crops outside PlantVillage, treatment prescription (advice is general), mobile apps, and training on field-collected data."
    )

    p("1.5 CHALLENGES", bold=True, size=14, space_before=16, space_after=6)
    p("1. Class confusion between visually similar tomato leaf-spot diseases.")
    p("2. Lab-quality training images versus real field photos.")
    p("3. Running a model and a database on a small, low-cost server.")
    p("4. Third-party LLM access: our first provider blocked the API project (HTTP 403), which led to a provider switch and a fallback design.")
    p("5. Serving an HTTPS page that calls an HTTP API (browser mixed-content blocking), solved with a CDN path-routing design.")
    p("6. Keeping credentials out of the code and the repository.")

    # =========================================================================
    # CHAPTER 2: BACKGROUND
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 2", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("BACKGROUND", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("2.1 LITERATURE SURVEY", bold=True, size=14, space_before=12, space_after=6)
    p(
        "Plant disease recognition: Hughes and Salathé (2015) released the PlantVillage image repository. Mohanty et al. (2016) "
        "trained deep CNNs on about 54,000 PlantVillage images across 38 classes, and reported very high accuracy on held-out lab "
        "images, but a large drop (to just above 31%) on images captured under different conditions. Ferentinos (2018) reported "
        "high success rates for CNN-based diagnosis across many plants and diseases, and Barbedo (2018) discussed how limited "
        "variety in image sources limits generalisation. These works motivate both our choice of dataset and our honest treatment "
        "of lab-versus-field accuracy."
    )
    p(
        "Efficient networks and transfer learning: Sandler et al. (2018) proposed MobileNetV2, which uses inverted residual blocks "
        "and depthwise separable convolutions to give strong accuracy at low computational cost. Pan and Yang (2010) survey "
        "transfer learning, where knowledge from a large source task is reused on a smaller target task. Jacob et al. (2018) "
        "describe quantisation, which shrinks models and speeds inference with a small accuracy cost."
    )
    p(
        "Confidence and rejection: Chow (1970) formalised the reject option, trading coverage for accuracy. Guo et al. (2017) "
        "showed modern networks can be over-confident, which is why our design uses a threshold and states its limits."
    )
    p(
        "Web services and security: Fielding (2000) defined REST. Jones et al. (2015) specified JSON Web Tokens (RFC 7519). "
        "Provos and Mazières (1999) introduced bcrypt for adaptive password hashing."
    )
    p(
        "Cloud models: Mell and Grance (2011) define IaaS, PaaS, and SaaS, which frame our deployment choices."
    )
    p(
        "Language models: Vaswani et al. (2017) introduced the transformer architecture behind current LLMs. Ji et al. (2023) "
        "survey hallucination, which motivates our curated fallback and disclaimer. Lewis et al. (2020) propose retrieval-augmented "
        "generation, our main future-work direction."
    )
    p(
        "Gap: Most plant-disease papers stop at model accuracy. Few present the end-to-end secured, deployed service with graceful "
        "degradation, which is this project's primary contribution."
    )

    p("2.2 REQUIREMENTS", bold=True, size=14, space_before=16, space_after=6)
    p("Table 2.1: Functional Requirements Specification", bold=True, size=11)
    t_f = doc.add_table(rows=1, cols=2)
    format_table(t_f, [Cm(3.0), Cm(12.0)], ["ID", "Functional Requirement Description"], [
        ["F1", "Register and log in users with bcrypt password hashing and JWT token issuance."],
        ["F2", "Accept a JPEG/PNG leaf photo and return a disease class and confidence score."],
        ["F3", "Return 'not sure' below the confidence threshold (0.70)."],
        ["F4", "Explain the disease (symptoms, causes, prevention) in plain language."],
        ["F5", "Save, list, view, update, and delete predictions per user (isolated CRUD)."],
        ["F6", "Store and return the uploaded photo via Amazon S3 object storage."],
        ["F7", "Publish interactive API documentation via OpenAPI/Swagger specification."]
    ])

    p("Table 2.2: Non-Functional Performance and Operational Targets", bold=True, size=11, space_before=14)
    t_nf = doc.add_table(rows=1, cols=2)
    format_table(t_nf, [Cm(5.0), Cm(10.0)], ["Non-Functional Requirement", "Target Metric and Strategy"], [
        ["Accuracy", "At least 90% on validation data; >= 95% on answered inputs."],
        ["Inference Time", "Under 100 ms per image on standard CPU."],
        ["Security", "Hashed passwords, token auth, per-user isolation, input validation."],
        ["Reliability", "Explanation falls back to local knowledge base if the LLM fails."],
        ["Availability", "Public HTTPS address, systemd auto-restart, CloudWatch monitoring."],
        ["Cost", "AWS free-tier resources (EC2, S3, CloudFront) and free LLM tier."]
    ])

    # =========================================================================
    # CHAPTER 3: METHODOLOGY
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 3", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("METHODOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("3.1 PROPOSED METHODOLOGY", bold=True, size=14, space_before=12, space_after=6)
    p(
        "3.1.1 Overall Architecture: The browser reaches Amazon CloudFront over HTTPS. CloudFront serves the page from a "
        "private S3 bucket and forwards /api/* to a FastAPI application on EC2. The application runs the TFLite CNN, stores data "
        "in SQLite, saves photos in a second S3 bucket through an IAM role, and calls an external LLM API. CloudWatch collects logs and metrics."
    )
    p(
        "3.1.2 Request Flow: Upload -> Validation (MIME type, size <= 5MB, readable image) -> CNN prediction -> Confidence check "
        "-> Explanation (LLM or fallback) -> Save to database and S3 -> Return JSON response."
    )
    p(
        "3.1.3 Model Design: MobileNetV2 with ImageNet weights is frozen and used as a feature extractor. A global average pooling "
        "layer, a 0.2 dropout layer, and a 38-way softmax layer are added (about 48,700 trainable parameters out of about 2.3 million). "
        "Rescaling and augmentation (horizontal flip, rotation up to about 36 degrees) are inside the model. It is trained with Adam "
        "and sparse categorical cross-entropy, batch size 32, for 6 epochs, then converted to TensorFlow Lite with dynamic-range (8-bit) quantisation."
    )
    p(
        "3.1.4 Confidence-Based Rejection: If the highest softmax probability is below 0.70, the API returns status 'uncertain' "
        "and does not generate an explanation, prompting the user for a clearer leaf photo."
    )
    p(
        "3.1.5 Explanation Module: The predicted class name is sent to an LLM with a prompt asking for JSON (summary, symptoms, "
        "causes, prevention), general guidance only, and no pesticide names or doses. The reply is validated. On any failure, "
        "including a 12-second timeout, the system returns the entry from a curated knowledge base of 38 entries. Each response states its source."
    )
    p(
        "3.1.6 API Design: Clean RESTful endpoints (/health, /classes, /auth/register, /auth/login, /auth/me, /predict, /predictions) "
        "with standard HTTP status codes (200, 201, 204, 400, 401, 404, 409, 413, 422, 502) and interactive OpenAPI documentation at /docs."
    )
    p(
        "3.1.7 Database Design: Table users (id, username unique, password hash, created time) and table predictions (id, user id as "
        "foreign key, disease, confidence, status, explanation JSON, note, S3 image key, created time), a one-to-many relationship with cascade delete."
    )
    p(
        "3.1.8 Security Design: bcrypt password hashing, JWT bearer tokens (60-minute expiry), ownership checks on every record "
        "(404 instead of 403 to avoid revealing other users' ids), upload type and 5 MB size limits, secrets in environment variables, "
        "and an IAM role instead of stored keys."
    )
    p(
        "3.1.9 Cloud Deployment and Service Models: EC2 runs the API and SQLite database (IaaS: full OS and process control). "
        "S3 hosts the static client and stores photos (Storage as a Service). CloudFront provides edge HTTPS distribution (CDN). "
        "Gemini provides natural language advisory (SaaS). CloudWatch provides centralized logs and alarms. EC2 was selected over Lambda "
        "because SQLite requires a persistent local file between runs."
    )
    p(
        "3.1.10 Provider, Registry, Consumer: The FastAPI service is the provider, its published OpenAPI description (/openapi.json, "
        "browsable at /docs) is the registry, and the web client, Swagger, and curl are consumers that discover and invoke the API."
    )
    p(
        "3.1.11 Testing: 11 automated pytest tests run against a temporary database with the LLM disabled, validating authentication, "
        "input sanitation, tenant isolation, and CRUD operations."
    )

    p("3.2 DATASETS", bold=True, size=14, space_before=16, space_after=6)
    p(
        "PlantVillage (Hughes and Salathé, 2015): 54,305 colour images, 38 classes covering 14 crops, split 80/20 with a fixed "
        "random seed (43,444 training, 10,861 validation). Images are resized to 224 x 224. The classes are imbalanced: the largest "
        "exceed 1,000 validation images (e.g. Orange Huanglongbing), while Potato healthy has only 25."
    )

    p("3.3 FLOW OF THE MODEL", bold=True, size=14, space_before=16, space_after=6)
    p(
        "The model execution pipeline: Raw Image Upload -> Bilinear Resize to 224x224 -> Pixel Rescaling [0, 255] -> Frozen MobileNetV2 "
        "Base (155 layers) -> Global Average Pooling (1280-dim feature vector) -> Dropout (0.2) -> 38-Way Dense Softmax Classifier "
        "-> Confidence Check (Threshold >= 0.70) -> Structured JSON Explanation Generation."
    )

    # =========================================================================
    # CHAPTER 4: RESULTS
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 4", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("RESULTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("4.1 EXPERIMENTAL SETUP", bold=True, size=14, space_before=12, space_after=6)
    p(
        "Training was executed on Google Colab with an Nvidia Tesla T4 GPU (16 GB VRAM). Evaluation of the converted TFLite model "
        "was performed on CPU in Colab using the same preprocessing pipeline as the deployed API. Production deployment was realized "
        "on an AWS EC2 Ubuntu 24.04 LTS instance in Mumbai (ap-south-1)."
    )

    p("4.2 RESULT SUMMARY TABLES", bold=True, size=14, space_before=16, space_after=6)
    p("Table 4.1: Classification Results (Held-Out Validation Set)", bold=True, size=11)
    t_41 = doc.add_table(rows=1, cols=2)
    format_table(t_41, [Cm(7.5), Cm(7.5)], ["Metric", "Measured Value"], [
        ["Keras Validation Accuracy (Float32)", "95.06%"],
        ["TFLite Validation Accuracy (Int8 Quantized)", "94.71% (95% CI 94.28 to 95.13)"],
        ["Macro-Average Recall", "0.928"],
        ["Macro-Average F1-Score", "0.933"],
        ["Model Inference Time (CPU)", "Mean 20.5 ms, p95 28.0 ms"]
    ])

    p("Table 4.2: Weakest Classes (Validation Set)", bold=True, size=11, space_before=14)
    t_42 = doc.add_table(rows=1, cols=5)
    format_table(t_42, [Cm(4.5), Cm(2.5), Cm(2.5), Cm(2.5), Cm(3.0)], ["Class Name", "Precision", "Recall", "F1", "Support (n)"], [
        ["Tomato Early blight", "0.878", "0.581", "0.699", "186"],
        ["Potato healthy", "1.000", "0.560", "0.718", "25"],
        ["Tomato Target Spot", "0.662", "0.871", "0.752", "279"],
        ["Tomato Spider mites", "0.945", "0.668", "0.782", "334"],
        ["Tomato Septoria leaf spot", "0.799", "0.890", "0.842", "335"]
    ])

    p("Table 4.3: Effect of the Confidence Threshold", bold=True, size=11, space_before=14)
    t_43 = doc.add_table(rows=1, cols=3)
    format_table(t_43, [Cm(4.0), Cm(5.5), Cm(5.5)], ["Threshold (tau)", "Images Answered (%)", "Accuracy on Answered"], [
        ["0.50", "98.0%", "95.7%"],
        ["0.60", "95.5%", "96.8%"],
        ["0.70 (Operational)", "92.9%", "97.6%"],
        ["0.80", "89.9%", "98.5%"],
        ["0.90", "85.2%", "99.2%"]
    ])

    p("Table 4.4: Automated System Tests Verification Matrix", bold=True, size=11, space_before=14)
    t_44 = doc.add_table(rows=1, cols=3)
    format_table(t_44, [Cm(5.0), Cm(7.0), Cm(3.0)], ["Test Function", "Tested Scenario", "Status"], [
        ["test_health", "System liveness verification", "11 of 11 Passed"],
        ["test_classes_lists_38", "Verify 38 class labels enumeration", "Passed"],
        ["test_register_and_duplicate", "Duplicate user 409 conflict check", "Passed"],
        ["test_register_validation", "Password minimum length validation", "Passed"],
        ["test_login_wrong_password", "Credential verification 401 check", "Passed"],
        ["test_me_requires_valid_token", "JWT authorization guard", "Passed"],
        ["test_predict_requires_login", "Unauthenticated upload block", "Passed"],
        ["test_predict_crud_flow", "End-to-end diagnosis and CRUD lifecycle", "Passed"],
        ["test_user_isolation", "Cross-tenant record isolation (404 check)", "Passed"]
    ])

    p("4.3 ANALYSIS OF RESULTS", bold=True, size=14, space_before=16, space_after=6)
    p(
        "The model separates most classes very well, with 14-crop coverage. Errors concentrate in the tomato block: Early blight "
        "is often confused with Septoria, Target Spot, and Bacterial spot, all of which produce brown leaf spots. Tomato healthy "
        "has high recall (0.99) but lower precision (0.82), which means some diseased leaves are predicted healthy, the more costly error. "
        "Accuracy rises steadily with the threshold, which shows that confidence carries information; our 0.70 setting trades about 7% "
        "coverage for about 3 points of accuracy. Quantisation cost about 0.35 percentage points (95.06% to 94.71%) in exchange for a "
        "much smaller, faster model (2.57 MB)."
    )

    p("4.4 COMPARISON WITH EXISTING METHODS", bold=True, size=14, space_before=16, space_after=6)
    p("These are authors' reported figures on different data and splits, so they are not directly comparable:")
    t_comp = doc.add_table(rows=1, cols=3)
    format_table(t_comp, [Cm(4.0), Cm(6.0), Cm(5.0)], ["Work", "Approach", "Reported Result"], [
        ["Mohanty et al. (2016)", "CNN on PlantVillage dataset", "Very high on lab images, ~31% on differently sourced images"],
        ["Plant Disease Advisor (Ours)", "Frozen MobileNetV2 features + quantised TFLite", "94.71% on held-out lab images (97.6% calibrated)"]
    ])
    p(
        "Our accuracy is slightly lower than the best published lab results because we train only a small head on a frozen small network, "
        "by design, to keep the model light enough for a low-cost server. Our contribution is the secured, deployed service around the model."
    )

    # =========================================================================
    # CHAPTER 5: INFERENCES
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 5", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("INFERENCES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("5.1 KEY FINDINGS", bold=True, size=14, space_before=12, space_after=6)
    p("1. A frozen MobileNetV2 with a small trained head reaches 94.7% on 38 classes with a model that runs in about 20 ms.")
    p("2. Rejecting low-confidence predictions improves reliability at a small cost in coverage.")
    p("3. Tomato leaf-spot diseases are the main source of error.")
    p("4. Graceful degradation kept the service available when our first LLM provider denied access.")
    p("5. The service can run on low-cost cloud resources with HTTPS, authentication, and monitoring.")

    p("5.2 INTERPRETATION OF RESULTS", bold=True, size=14, space_before=16, space_after=6)
    p(
        "The confusion pattern matches what is visible to the eye: several diseases differ mainly in the pattern of brown spots, "
        "and a frozen general-purpose feature extractor has limited ability to separate them. Fine-tuning the base network and adding "
        "field photographs should help. The high lab accuracy should not be read as field accuracy, because PlantVillage images have "
        "uniform backgrounds, and several photos of one leaf may appear on both sides of the split."
    )

    p("5.3 IMPLICATIONS OF THE STUDY", bold=True, size=14, space_before=16, space_after=6)
    p("1. A small team can offer AI diagnosis as a web service with a modest cloud budget.")
    p("2. The LLM-plus-fallback pattern is a general way to use an unreliable third-party service safely.")
    p(
        "3. Service-model trade-off: EC2 (IaaS) gives full control and keeps a local database, at the cost of managing the operating "
        "system and process. A serverless (Lambda) design removes server management but would need a managed database, and a PaaS option "
        "would reduce operations further but gives less control over the runtime."
    )

    p("5.4 FULFILLMENT OF OBJECTIVES (PROVED BY STATISTICAL METHODS)", bold=True, size=14, space_before=16, space_after=6)
    t_obj = doc.add_table(rows=1, cols=4)
    format_table(t_obj, [Cm(3.5), Cm(3.0), Cm(3.5), Cm(5.0)], ["Objective", "Target", "Result", "Statistical Evidence"], [
        ["1. Accuracy", "At least 90%", "94.71%", "95% CI 94.28 to 95.13 (n = 10,861; lower bound > 90%, p < 0.0001)."],
        ["2. Inference Time", "Under 100 ms", "Mean 20.5 ms (p95 28.0 ms)", "n = 10,861 CPU executions; satisfies target by 3.5x margin."],
        ["3. Reliability", "At least 95%", "97.6% on 92.9% images", "Approximate 95% CI 97.3 to 97.9 (n ~ 10,090 answered)."],
        ["4. Secure CRUD", "All tests pass", "11 of 11 passed", "Automated pytest verification suite."],
        ["5. Cloud Deploy", "Deployed & monitored", "Live on AWS", "Deployed on EC2, S3, CloudFront, IAM, CloudWatch."]
    ])
    p(
        "Statistical Method: Binomial proportion confidence intervals (normal approximation; the Wilson interval, Wilson 1927, "
        "is suitable for small samples). Accuracy, precision, recall, and F1 are computed directly from the confusion matrix.",
        space_before=6
    )

    # =========================================================================
    # CHAPTER 6: CONCLUSION
    # ==========================================
    doc.add_page_break()
    p("CHAPTER 6", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=4)
    p("CONCLUSION & FUTURE WORK", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("6.1 RESULTS", bold=True, size=14, space_before=12, space_after=6)
    p(
        "The project delivers a working, secured, cloud-deployed REST service that identifies 38 plant diseases at 94.7% validation "
        "accuracy, rejects uncertain inputs, explains diagnoses, and keeps each user's history privately. All five objectives were "
        "evaluated and met on statistical evidence."
    )
    p(
        "Limitations: Only 38 PlantVillage classes; lab-image bias; some diseased tomato leaves predicted healthy; LLM text may "
        "vary or be wrong, so it is accompanied by a disclaimer; the demo server's API port is open and CORS is permissive."
    )

    p("6.2 FUTURE WORK", bold=True, size=14, space_before=16, space_after=6)
    p("1. Retrieval-augmented explanations grounded in agricultural documents, with citations (Lewis et al., 2020).")
    p("2. Fine-tune the base network and add field-collected images.")
    p("3. Containerise the service with Docker, and restrict network access so only CloudFront reaches the server.")
    p("4. Per-class thresholds and probability calibration.")
    p("5. Support more crops and regional languages.")

    p("6.3 REFERENCES (APA FORMAT)", bold=True, size=14, space_before=16, space_after=6)
    refs_apa = [
        "Amazon Web Services. (2026). AWS documentation (EC2, S3, CloudFront, IAM, CloudWatch). https://docs.aws.amazon.com",
        "Barbedo, J. G. A. (2018). Impact of dataset size and variety on the effectiveness of deep learning and transfer learning for plant disease classification. Computers and Electronics in Agriculture, 153, 46-53.",
        "Chow, C. K. (1970). On optimum recognition error and reject tradeoff. IEEE Transactions on Information Theory, 16(1), 41-46.",
        "Ferentinos, K. P. (2018). Deep learning models for plant disease detection and diagnosis. Computers and Electronics in Agriculture, 145, 311-318.",
        "Fielding, R. T. (2000). Architectural styles and the design of network-based software architectures [Doctoral dissertation, University of California, Irvine].",
        "Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. Proceedings of ICML, 70, 1321-1330.",
        "Hughes, D. P., & Salathé, M. (2015). An open access repository of images on plant health to enable the development of mobile disease diagnostics. arXiv:1511.08060.",
        "Jacob, B., et al. (2018). Quantization and training of neural networks for efficient integer-arithmetic-only inference. Proceedings of CVPR, 2704-2713.",
        "Ji, Z., et al. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), 1-38.",
        "Jones, M., Bradley, J., & Sakimura, N. (2015). JSON Web Token (JWT) (RFC 7519). IETF.",
        "Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459-9474.",
        "Mell, P., & Grance, T. (2011). The NIST definition of cloud computing (SP 800-145). NIST.",
        "Mohanty, S. P., Hughes, D. P., & Salathé, M. (2016). Using deep learning for image-based plant disease detection. Frontiers in Plant Science, 7, 1419.",
        "Pan, S. J., & Yang, Q. (2010). A survey on transfer learning. IEEE Transactions on Knowledge and Data Engineering, 22(10), 1345-1359.",
        "Provos, N., & Mazières, D. (1999). A future-adaptable password scheme. Proceedings of USENIX Annual Technical Conference, 81-91.",
        "Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L.-C. (2018). MobileNetV2: Inverted residuals and linear bottlenecks. Proceedings of CVPR, 4510-4520.",
        "Vaswani, A., et al. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998-6008.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209-212."
    ]
    for r in refs_apa:
        p_ref = p(r, space_after=4)
        p_ref.paragraph_format.left_indent = Inches(0.5)
        p_ref.paragraph_format.first_line_indent = Inches(-0.5)

    # =========================================================================
    # APPENDIX
    # ==========================================
    doc.add_page_break()
    p("APPENDIX", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=18)
    p("A. Key source code listings (app.py, auth.py, predict.py, explain.py, database.py, models.py).", bold=True)
    p("B. Full API reference with sample requests, response schemas, and OpenAPI endpoints.")
    p("C. Screenshots index: Swagger /docs, CRUD in action, 'uncertain' threshold alert, SQLite tables, 401/404 security checks, Pytest 11/11 output, S3 buckets, CloudFront behaviors, IAM role, EC2 instance, CloudWatch metrics.")
    p("D. Environment variables table (.env) and deployment configuration.")
    p("E. Full per-class precision/recall/F1 table and confusion matrix analysis.")

    # Save to both paths
    out1 = "F:/plant-disease-advisor/Plant_Disease_Advisor_Project_Report.docx"
    out2 = "C:/Users/Lenovo/.gemini/antigravity/brain/d0f7aa48-18af-4616-9516-ecd64527d2d6/Plant_Disease_Advisor_Project_Report.docx"
    doc.save(out1)
    doc.save(out2)
    print(f"Report regenerated successfully at {out1} and {out2}")

if __name__ == "__main__":
    generate_rvu_report()
