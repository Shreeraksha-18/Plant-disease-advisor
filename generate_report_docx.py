import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_page_number_footer(section):
    """Add centered page number field to section footer."""
    footer = section.footer
    footer.is_linked_to_previous = False
    # Clear existing
    for para in footer.paragraphs:
        for run in para.runs:
            run.clear()
    if footer.paragraphs:
        fp = footer.paragraphs[0]
    else:
        fp = footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(0)
    fp.paragraph_format.space_after = Pt(0)
    run = fp.add_run()
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    # Insert PAGE field
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    run._r.append(fldChar1)
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    run._r.append(instrText)
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar2)

def generate_rvu_report():
    doc = Document()

    # ── Page Setup ──
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.81)
    sec.right_margin = Cm(2.54)
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    # Add page numbers (Arabic, bottom center) to first section
    add_page_number_footer(sec)

    # ── Base Style: TNR 12pt, 1.5 line spacing, justified ──
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.widow_control = True   # no orphan opening lines

    # ── Helper: add a paragraph ──
    def p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False,
          size=12, space_after=6, space_before=0, underline=False, line_spacing=1.5):
        para = doc.add_paragraph()
        para.alignment = align
        para.paragraph_format.space_before = Pt(space_before)
        para.paragraph_format.space_after = Pt(space_after)
        para.paragraph_format.line_spacing = line_spacing
        para.paragraph_format.widow_control = True
        if text:
            run = para.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(size)
            run.bold = bold
            run.italic = italic
            run.underline = underline
            run.font.color.rgb = RGBColor(0, 0, 0)
        return para

    # ── Helper: Chapter Heading (16pt, Bold, TNR) ──
    def chapter_heading(chap_num, title):
        doc.add_page_break()
        p(f"CHAPTER {chap_num}", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=24, space_after=4)
        p(title.upper(), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    # ── Helper: Section Heading (14pt, TNR, CAPS) ──
    def section_heading(text):
        p(text.upper(), align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, size=14, space_before=14, space_after=6)

    # ── Helper: Subsection Heading (12pt, TNR, CAPS) ──
    def subsection_heading(text):
        p(text.upper(), align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, size=12, space_before=10, space_after=4)

    # ── Helper: format a table (10pt captions, single spacing inside) ──
    def format_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            pa = hdr_cells[i].paragraphs[0]
            pa.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pa.paragraph_format.line_spacing = 1.0  # single spaced in tables
            pa.paragraph_format.space_before = Pt(2)
            pa.paragraph_format.space_after = Pt(2)
            pa.runs[0].font.name = 'Times New Roman'
            pa.runs[0].font.size = Pt(10)
            pa.runs[0].bold = True
            shading = parse_xml(r'<w:shd {} w:fill="F2F4F3"/>'.format(nsdecls('w')))
            hdr_cells[i]._tc.get_or_add_tcPr().append(shading)
        for row_data in data:
            row_cells = table.add_row().cells
            for i, val in enumerate(row_data):
                row_cells[i].text = str(val)
                pa = row_cells[i].paragraphs[0]
                pa.alignment = WD_ALIGN_PARAGRAPH.LEFT
                pa.paragraph_format.line_spacing = 1.0
                pa.paragraph_format.space_before = Pt(2)
                pa.paragraph_format.space_after = Pt(2)
                if len(pa.runs) > 0:
                    pa.runs[0].font.name = 'Times New Roman'
                    pa.runs[0].font.size = Pt(10)
        for row in table.rows:
            for i, cell in enumerate(row.cells):
                cell.width = col_widths[i]
                set_cell_margins(cell, 60, 60, 100, 100)
                tcPr = cell._tc.get_or_add_tcPr()
                borders = parse_xml(
                    r'<w:tcBorders {}><w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:left w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
                    r'<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/></w:tcBorders>'.format(nsdecls('w'))
                )
                tcPr.append(borders)

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE  (left exactly as-is per template typography)
    # ══════════════════════════════════════════════════════════════════════════
    p("School of Computer Science and Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=24, space_after=18)
    p("OCTOBER, 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_after=36)

    # Title: Times New Roman, Font 20, Bold, CAPS
    p("PLANT DISEASE ADVISOR: A CLOUD-DEPLOYED RESTFUL WEB SERVICE FOR CNN-BASED LEAF DISEASE DIAGNOSIS WITH LLM-GENERATED EXPLANATIONS",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=20, space_after=36)

    # Submitted...: Times New Roman, Font 14, Italic
    p("Submitted in partial fulfillment for the award of the degree of",
      align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=12)

    # Degree name: Times New Roman, Font 22, Bold
    p("Bachelor of Technology (Honours) in Computer Science and Engineering",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=22, space_after=36)

    # by: Times New Roman, Font 14, Italic
    p("by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=12)

    # Candidate name + USN: Times New Roman, Font 16, Bold, CAPS
    p("[NAME OF THE CANDIDATE]\nUSN: [1RVXXXXXXXX]",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=36)

    # Guided by
    p("Guided by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=14, space_after=8)

    # Guide: Times New Roman, Font 16, Bold, CAPS
    p("[GUIDE NAME]\nDESIGNATION, SOCSE, RV UNIVERSITY",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=0)

    # ══════════════════════════════════════════════════════════════════════════
    # CERTIFICATE  (left exactly as-is per template)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("School of Computer Science and Engineering\nRV University\nRV Vidyaniketan, 8th Mile, Mysore Road, Bengaluru, Karnataka, India - 560059",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=12, space_after=30)

    p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=24)

    p("This is to certify that the project work titled \"PLANT DISEASE ADVISOR: A CLOUD-DEPLOYED RESTFUL WEB SERVICE "
      "FOR CNN-BASED LEAF DISEASE DIAGNOSIS WITH LLM-GENERATED EXPLANATIONS\" has been carried out by [Name of Candidate], "
      "bearing USN: [1RVXXXXXXXX], a bonafide student of the Bachelor of Technology (Honours) in Computer Science and "
      "Engineering programme at the School of Computer Science and Engineering, RV University, Bengaluru, in partial "
      "fulfillment of the requirements for the award of the degree of Bachelor of Technology (Honours) in Computer Science "
      "and Engineering during the academic year 2026\u20132027.", space_after=48)

    t_eval = doc.add_table(rows=3, cols=2)
    format_table(t_eval, [Cm(7.5), Cm(7.5)],
                 ["Name of the Examiner", "Signature of Examiner"],
                 [["1. __________________________________", "1. __________________________________"],
                  ["2. __________________________________", "2. __________________________________"]])

    # ══════════════════════════════════════════════════════════════════════════
    # ABSTRACT  (page i)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, underline=True, space_before=12, space_after=20)

    p("Plant diseases reduce crop yield, and farmers often lack quick access to expert diagnosis. This project presents "
      "Plant Disease Advisor, a RESTful web service that identifies a leaf disease from a photograph and explains it in plain "
      "language. A MobileNetV2 convolutional neural network, adapted by transfer learning on the PlantVillage dataset "
      "(38 classes, 14 crops), classifies the image and achieves 94.71% accuracy (95% CI 94.28 to 95.13) on 10,861 held-out "
      "validation images. Predictions below a 0.70 confidence threshold are rejected, which raises accuracy on the answered "
      "images to 97.6%. A large language model generates the explanation, with automatic fallback to a curated knowledge base "
      "when the model is unavailable.")

    p("The service provides user registration, JWT authentication, per-user storage of predictions in a relational database, "
      "photo storage in Amazon S3, and full CRUD endpoints documented with OpenAPI. It is deployed on AWS using EC2, S3, "
      "CloudFront, IAM, and CloudWatch. The work demonstrates web service design, security, testing, and cloud service "
      "models in a single working system.")

    p("Keywords: REST API, transfer learning, MobileNetV2, plant disease, AWS, cloud service models.", bold=True, space_before=18)

    # ══════════════════════════════════════════════════════════════════════════
    # ACKNOWLEDGMENT  (page ii)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("ACKNOWLEDGMENT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, underline=True, space_before=12, space_after=20)

    p("It is my pleasure to express with deep sense of gratitude to [Internal Guide Name], [Designation], School of Computer "
      "Science and Engineering, RV University, for their constant guidance, continual encouragement, understanding; more than all, "
      "they taught me patience in my endeavor. My association with them is not confined to academics only, but it is a great "
      "opportunity on my part of work with an intellectual and expert in the field of Computer Science and Cloud Computing.")

    p("I would like to express my gratitude to Dr Ram Kumar Kakani, Vice Chancellor RV University, and Dr Shobha G, Dean SoCSE, "
      "RV University, for providing with an environment to work in and for their inspiration during the tenure of the course.")

    p("I express my sincere gratitude to [Program Director Name], Program Director, B.Tech (H), School of Computer Science & Engineering, "
      "RV University, for the guidance and support provided throughout my course of study. I also extend my heartfelt thanks to all "
      "the faculty members and staff of the School for their constant encouragement, valuable guidance, and assistance, which contributed "
      "significantly to the successful completion of my studies. Finally, I would like to express my deepest gratitude to my parents "
      "for their unwavering support, encouragement, and belief in me throughout this journey.")

    p("It is indeed a pleasure to thank my friends who persuaded and encouraged me to take up and complete this task. At last but "
      "not least, I express my gratitude and appreciation to all those who have helped me directly or indirectly toward the "
      "successful completion of this project.")

    p("Place: Bangalore\nDate: [Date]", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, space_before=24, space_after=0)
    p("[Name of the Student]\nUSN: [1RVXXXXXXXX]", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, space_before=0, space_after=0)

    # ══════════════════════════════════════════════════════════════════════════
    # CONTENTS  (single spaced lines, as per formatting rules)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)

    toc_items = [
        ("ABSTRACT", "i"), ("ACKNOWLEDGMENT", "ii"), ("CONTENTS", "iii"),
        ("LIST OF FIGURES", "vi"), ("LIST OF TABLES", "vii"), ("LIST OF ACRONYMS", "viii"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1 INTRODUCTION", "1"), ("    1.2 AIM AND OBJECTIVES", "3"),
        ("    1.3 PROBLEM STATEMENT", "4"), ("    1.4 SCOPE OF THE PROJECT", "5"),
        ("    1.5 CHALLENGES", "6"),
        ("CHAPTER 2: BACKGROUND", "10"),
        ("    2.1 LITERATURE SURVEY", "10"), ("    2.2 REQUIREMENTS", "15"),
        ("CHAPTER 3: METHODOLOGY", "17"),
        ("    3.1 PROPOSED METHODOLOGY", "17"), ("    3.2 DATASETS", "19"),
        ("    3.3 FLOW OF THE MODEL", "20"),
        ("CHAPTER 4: RESULTS", "25"),
        ("    4.1 EXPERIMENTAL SETUP", "25"), ("    4.2 RESULT SUMMARY TABLES", "27"),
        ("    4.3 ANALYSIS OF RESULTS", "29"), ("    4.4 COMPARISON WITH EXISTING METHODS", "30"),
        ("CHAPTER 5: INFERENCES", "35"),
        ("    5.1 KEY FINDINGS", "35"), ("    5.2 INTERPRETATION OF RESULTS", "38"),
        ("    5.3 IMPLICATIONS OF THE STUDY", "39"), ("    5.4 FULFILLMENT OF OBJECTIVES", "41"),
        ("CHAPTER 6: CONCLUSION", "43"),
        ("    6.1 RESULTS", "43"), ("    6.2 FUTURE WORK", "45"),
        ("    6.3 REFERENCES", "46"),
        ("APPENDIX", "47"),
    ]
    for item, pg in toc_items:
        is_chapter = item.startswith("CHAPTER") or item in ("ABSTRACT", "ACKNOWLEDGMENT", "CONTENTS",
                                                             "LIST OF FIGURES", "LIST OF TABLES",
                                                             "LIST OF ACRONYMS", "APPENDIX")
        pa = p(f"{item}{'.' * max(3, 70 - len(item))}{pg}",
               align=WD_ALIGN_PARAGRAPH.LEFT, bold=is_chapter, size=12,
               space_after=2, space_before=1, line_spacing=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # LIST OF FIGURES  (single spaced)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("LIST OF FIGURES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    figs = [
        ("3.1 HIGH-LEVEL CLOUD-NATIVE SYSTEM ARCHITECTURE DIAGRAM", "18"),
        ("3.2 SYNCHRONOUS DIAGNOSTIC REQUEST SEQUENCE FLOW", "19"),
        ("3.3 MOBILENETV2 ARCHITECTURE AND CLASSIFICATION HEAD", "21"),
        ("3.4 DUAL-ENGINE EXPLANATION FLOW WITH AUTOMATIC FALLBACK", "22"),
        ("3.5 RELATIONAL DATABASE ENTITY-RELATIONSHIP (ER) DIAGRAM", "23"),
        ("3.6 MACHINE LEARNING PROCESSING PIPELINE FLOWCHART", "24"),
    ]
    for title, pg in figs:
        p(f"{title}{'.' * max(3, 60 - len(title))}{pg}",
          align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_after=2, space_before=1, line_spacing=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # LIST OF TABLES  (single spaced)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("LIST OF TABLES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    tables_list = [
        ("2.1 FUNCTIONAL REQUIREMENTS SPECIFICATION", "15"),
        ("2.2 NON-FUNCTIONAL OPERATIONAL REQUIREMENTS", "16"),
        ("3.1 AWS CLOUD COMPONENTS AND NIST SERVICE MODELS", "24"),
        ("4.1 CLASSIFICATION RESULTS ON HELD-OUT VALIDATION SET", "27"),
        ("4.2 WEAKEST CLASSES EVALUATION PROFILE", "28"),
        ("4.3 EFFECT OF THE CONFIDENCE THRESHOLD ON ACCURACY", "28"),
        ("4.4 AUTOMATED PYTEST SUITE TEST VERIFICATION MATRIX", "29"),
        ("4.5 COMPARISON WITH PUBLISHED PLANT DISEASE METHODS", "31"),
        ("5.1 STATISTICAL HYPOTHESIS VERIFICATION OF OBJECTIVES", "41"),
    ]
    for title, pg in tables_list:
        p(f"{title}{'.' * max(3, 60 - len(title))}{pg}",
          align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_after=2, space_before=1, line_spacing=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # LIST OF ACRONYMS  (single spaced inside table)
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("LIST OF ACRONYMS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=12, space_after=18)
    t_acro = doc.add_table(rows=1, cols=2)
    format_table(t_acro, [Cm(4.0), Cm(11.0)], ["Acronym", "Full Form"], [
        ["API", "Application Programming Interface"],
        ["AWS", "Amazon Web Services"],
        ["CDN", "Content Delivery Network"],
        ["CI", "Confidence Interval"],
        ["CNN", "Convolutional Neural Network"],
        ["CRUD", "Create, Read, Update, Delete"],
        ["EC2", "Elastic Compute Cloud"],
        ["F1", "Harmonic Mean of Precision and Recall"],
        ["IaaS", "Infrastructure as a Service"],
        ["JWT", "JSON Web Token (RFC 7519)"],
        ["LLM", "Large Language Model"],
        ["PaaS", "Platform as a Service"],
        ["RAG", "Retrieval-Augmented Generation"],
        ["REST", "Representational State Transfer"],
        ["S3", "Simple Storage Service"],
        ["SaaS", "Software as a Service"],
        ["SOA", "Service-Oriented Architecture"],
        ["TFLite", "TensorFlow Lite"],
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 1: INTRODUCTION
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(1, "Introduction")

    # Section Heading: 14pt, TNR, CAPS (NOT bold per spec)
    section_heading("1.1 Introduction")
    p("Crop diseases cause significant yield loss, and early identification limits their spread. Expert diagnosis is not "
      "always available to small farmers. Deep learning can classify disease from leaf images, but a trained model has no "
      "value to a farmer until it is packaged as a service people can reach. This project turns an image classifier into a "
      "secure, documented, cloud-hosted web service, and adds an LLM-generated explanation so that the output is understandable "
      "and actionable.")

    section_heading("1.2 Aim and Objectives")
    p("Aim: to design, implement, and deploy a RESTful web service that diagnoses plant leaf diseases from images and explains them.")
    p("Objectives (each is measured in Chapter 5):")
    p("1. Classify leaf images into 38 classes with at least 90% accuracy on held-out data.")
    p("2. Keep model inference time under 100 ms per image on general-purpose CPU hardware.")
    p("3. Reject uncertain predictions so that accuracy on answered images is at least 95%.")
    p("4. Provide authenticated CRUD endpoints with per-user data isolation, verified by automated tests.")
    p("5. Deploy the system on AWS using appropriate cloud service models and monitor it.")

    section_heading("1.3 Problem Statement")
    p("There is no simple, secure, publicly reachable service that returns both a disease diagnosis and an understandable "
      "explanation from a leaf photo, and that reports when it is not sure instead of guessing.")

    section_heading("1.4 Scope of the Project")
    p("In scope: 38 PlantVillage classes (14 crops), a REST API, a web client, a database, cloud deployment, and monitoring. "
      "Out of scope: crops outside PlantVillage, treatment prescription (advice is general), mobile apps, and training on field-collected data.")

    section_heading("1.5 Challenges")
    p("1. Class confusion between visually similar tomato leaf-spot diseases.")
    p("2. Lab-quality training images versus real field photos.")
    p("3. Running a model and a database on a small, low-cost server.")
    p("4. Third-party LLM access: our first provider blocked the API project (HTTP 403), which led to a provider switch and a fallback design.")
    p("5. Serving an HTTPS page that calls an HTTP API (browser mixed-content blocking), solved with a CDN path-routing design.")
    p("6. Keeping credentials out of the code and the repository.")

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 2: BACKGROUND
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(2, "Background")

    section_heading("2.1 Literature Survey")

    subsection_heading("2.1.1 Plant Disease Recognition via Deep Learning")
    p("Hughes and Salath\u00e9 (2015) released the PlantVillage image repository. Mohanty et al. (2016) "
      "trained deep CNNs on about 54,000 PlantVillage images across 38 classes, and reported very high accuracy on held-out lab "
      "images, but a large drop (to just above 31%) on images captured under different conditions. Ferentinos (2018) reported "
      "high success rates for CNN-based diagnosis across many plants and diseases, and Barbedo (2018) discussed how limited "
      "variety in image sources limits generalisation. These works motivate both our choice of dataset and our honest treatment "
      "of lab-versus-field accuracy.")

    subsection_heading("2.1.2 Efficient Networks, Transfer Learning, and Quantization")
    p("Sandler et al. (2018) proposed MobileNetV2, which uses inverted residual blocks "
      "and depthwise separable convolutions to give strong accuracy at low computational cost. Pan and Yang (2010) survey "
      "transfer learning, where knowledge from a large source task is reused on a smaller target task. Jacob et al. (2018) "
      "describe quantisation, which shrinks models and speeds inference with a small accuracy cost.")

    subsection_heading("2.1.3 Confidence and Rejection")
    p("Chow (1970) formalised the reject option, trading coverage for accuracy. Guo et al. (2017) "
      "showed modern networks can be over-confident, which is why our design uses a threshold and states its limits.")

    subsection_heading("2.1.4 Web Services and Security")
    p("Fielding (2000) defined REST. Jones et al. (2015) specified JSON Web Tokens (RFC 7519). "
      "Provos and Mazi\u00e8res (1999) introduced bcrypt for adaptive password hashing.")

    subsection_heading("2.1.5 Cloud Models")
    p("Mell and Grance (2011) define IaaS, PaaS, and SaaS, which frame our deployment choices.")

    subsection_heading("2.1.6 Language Models")
    p("Vaswani et al. (2017) introduced the transformer architecture behind current LLMs. Ji et al. (2023) "
      "survey hallucination, which motivates our curated fallback and disclaimer. Lewis et al. (2020) propose retrieval-augmented "
      "generation, our main future-work direction.")

    subsection_heading("2.1.7 Research Gap")
    p("Most plant-disease papers stop at model accuracy. Few present the end-to-end secured, deployed service with graceful "
      "degradation, which is this project\u2019s primary contribution.")

    section_heading("2.2 Requirements")

    # Table caption in 10pt
    p("Table 2.1: Functional Requirements Specification", size=10, italic=True, space_before=6, space_after=4)
    t_f = doc.add_table(rows=1, cols=2)
    format_table(t_f, [Cm(3.0), Cm(12.0)], ["ID", "Functional Requirement Description"], [
        ["F1", "Register and log in users with bcrypt password hashing and JWT token issuance."],
        ["F2", "Accept a JPEG/PNG leaf photo and return a disease class and confidence score."],
        ["F3", "Return \u2018not sure\u2019 below the confidence threshold (0.70)."],
        ["F4", "Explain the disease (symptoms, causes, prevention) in plain language."],
        ["F5", "Save, list, view, update, and delete predictions per user (isolated CRUD)."],
        ["F6", "Store and return the uploaded photo via Amazon S3 object storage."],
        ["F7", "Publish interactive API documentation via OpenAPI/Swagger specification."],
    ])

    p("Table 2.2: Non-Functional Performance and Operational Targets", size=10, italic=True, space_before=14, space_after=4)
    t_nf = doc.add_table(rows=1, cols=2)
    format_table(t_nf, [Cm(5.0), Cm(10.0)], ["Requirement", "Target"], [
        ["Accuracy", "At least 90% on validation data; \u2265 95% on answered inputs."],
        ["Inference Time", "Under 100 ms per image on standard CPU."],
        ["Security", "Hashed passwords, token auth, per-user isolation, input validation."],
        ["Reliability", "Explanation falls back to local knowledge base if the LLM fails."],
        ["Availability", "Public HTTPS address, systemd auto-restart, CloudWatch monitoring."],
        ["Cost", "AWS free-tier resources (EC2, S3, CloudFront) and free LLM tier."],
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 3: METHODOLOGY
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(3, "Methodology")

    section_heading("3.1 Proposed Methodology")

    subsection_heading("3.1.1 Overall Architecture")
    p("The browser reaches Amazon CloudFront over HTTPS. CloudFront serves the page from a "
      "private S3 bucket and forwards /api/* to a FastAPI application on EC2. The application runs the TFLite CNN, stores data "
      "in SQLite, saves photos in a second S3 bucket through an IAM role, and calls an external LLM API. CloudWatch collects logs and metrics.")

    subsection_heading("3.1.2 Request Flow")
    p("Upload \u2192 Validation (MIME type, size \u2264 5 MB, readable image) \u2192 CNN prediction \u2192 Confidence check "
      "\u2192 Explanation (LLM or fallback) \u2192 Save to database and S3 \u2192 Return JSON response.")

    subsection_heading("3.1.3 Model Design")
    p("MobileNetV2 with ImageNet weights is frozen and used as a feature extractor. A global average pooling "
      "layer, a 0.2 dropout layer, and a 38-way softmax layer are added (about 48,700 trainable parameters out of about 2.3 million). "
      "Rescaling and augmentation (horizontal flip, rotation up to about 36 degrees) are inside the model. It is trained with Adam "
      "and sparse categorical cross-entropy, batch size 32, for 6 epochs, then converted to TensorFlow Lite with dynamic-range (8-bit) quantisation.")

    subsection_heading("3.1.4 Confidence-Based Rejection")
    p("If the highest softmax probability is below 0.70, the API returns status \u2018uncertain\u2019 "
      "and does not generate an explanation, prompting the user for a clearer leaf photo.")

    subsection_heading("3.1.5 Explanation Module")
    p("The predicted class name is sent to an LLM with a prompt asking for JSON (summary, symptoms, "
      "causes, prevention), general guidance only, and no pesticide names or doses. The reply is validated. On any failure, "
      "including a 12-second timeout, the system returns the entry from a curated knowledge base of 38 entries. Each response states its source.")

    subsection_heading("3.1.6 API Design")
    p("Clean RESTful endpoints (/health, /classes, /auth/register, /auth/login, /auth/me, /predict, /predictions) "
      "with standard HTTP status codes (200, 201, 204, 400, 401, 404, 409, 413, 422, 502) and interactive OpenAPI documentation at /docs.")

    subsection_heading("3.1.7 Database Design")
    p("Table users (id, username unique, password hash, created time) and table predictions (id, user id as "
      "foreign key, disease, confidence, status, explanation JSON, note, S3 image key, created time), a one-to-many relationship with cascade delete.")

    subsection_heading("3.1.8 Security Design")
    p("bcrypt password hashing, JWT bearer tokens (60-minute expiry), ownership checks on every record "
      "(404 instead of 403 to avoid revealing other users\u2019 ids), upload type and 5 MB size limits, secrets in environment variables, "
      "and an IAM role instead of stored keys.")

    subsection_heading("3.1.9 Cloud Deployment and Service Models")
    p("Table 3.1: AWS Cloud Components and NIST Service Models", size=10, italic=True, space_before=4, space_after=4)
    t_cloud = doc.add_table(rows=1, cols=3)
    format_table(t_cloud, [Cm(4.0), Cm(6.0), Cm(5.0)], ["AWS Component", "Role", "Service Model"], [
        ["EC2 (Ubuntu, systemd)", "Runs the API, model, and database", "IaaS"],
        ["S3 web bucket + CloudFront", "Hosts the page, HTTPS, single address", "Object storage + CDN"],
        ["S3 data bucket + IAM role", "Photo storage without stored keys", "Storage as a service"],
        ["LLM API (Gemini)", "Generates explanations", "SaaS"],
        ["CloudWatch", "Logs and CPU alarm", "Managed monitoring"],
    ])
    p("Why EC2 and not Lambda: the application keeps a SQLite database file, and Lambda does not preserve local files between "
      "invocations, so a serverless design would have required moving to a managed database.", space_before=8)

    subsection_heading("3.1.10 Provider, Registry, Consumer")
    p("The FastAPI service is the provider, its published OpenAPI description (/openapi.json, browsable at /docs) is the registry, "
      "and the web client, Swagger, and curl are consumers that read that description and invoke the API.")

    subsection_heading("3.1.11 Testing")
    p("11 automated pytest tests run against a temporary database with the LLM disabled, validating authentication, "
      "input sanitation, tenant isolation, and CRUD operations.")

    section_heading("3.2 Datasets")
    p("PlantVillage (Hughes and Salath\u00e9, 2015): 54,305 colour images, 38 classes covering 14 crops, split 80/20 with a fixed "
      "random seed (43,444 training, 10,861 validation). Images are resized to 224 \u00d7 224. The classes are imbalanced: the largest "
      "exceed 1,000 validation images (e.g. Orange Huanglongbing), while Potato healthy has only 25.")

    section_heading("3.3 Flow of the Model")
    p("Raw Image Upload \u2192 Bilinear Resize to 224\u00d7224 \u2192 Pixel Values [0, 255] \u2192 Frozen MobileNetV2 "
      "Base (155 layers) \u2192 Global Average Pooling (1280-dim vector) \u2192 Dropout (0.2) \u2192 38-Way Dense Softmax Classifier "
      "\u2192 Confidence Check (Threshold \u2265 0.70) \u2192 Structured JSON Explanation Generation.")

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 4: RESULTS
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(4, "Results")

    section_heading("4.1 Experimental Setup")
    p("Training was executed on Google Colab with an Nvidia Tesla T4 GPU (16 GB VRAM). Evaluation of the converted TFLite model "
      "was performed on CPU in Colab using the same preprocessing pipeline as the deployed API. Production deployment was realised "
      "on an AWS EC2 Ubuntu 24.04 LTS instance in Mumbai (ap-south-1).")

    section_heading("4.2 Result Summary Tables")

    p("Table 4.1: Classification Results", size=10, italic=True, space_before=6, space_after=4)
    t_41 = doc.add_table(rows=1, cols=2)
    format_table(t_41, [Cm(7.5), Cm(7.5)], ["Metric", "Value"], [
        ["Keras validation accuracy", "95.06%"],
        ["TFLite validation accuracy", "94.71% (95% CI 94.28 to 95.13)"],
        ["Macro-average recall", "0.928"],
        ["Macro-average F1", "0.933"],
        ["Model inference time (CPU)", "Mean 20.5 ms, p95 28.0 ms"],
    ])

    p("Table 4.2: Weakest Classes (Validation Set)", size=10, italic=True, space_before=14, space_after=4)
    t_42 = doc.add_table(rows=1, cols=5)
    format_table(t_42, [Cm(4.5), Cm(2.5), Cm(2.5), Cm(2.5), Cm(3.0)],
                 ["Class", "Precision", "Recall", "F1", "Support"], [
        ["Tomato Early blight", "0.878", "0.581", "0.699", "186"],
        ["Potato healthy", "1.000", "0.560", "0.718", "25"],
        ["Tomato Target Spot", "0.662", "0.871", "0.752", "279"],
        ["Tomato Spider mites", "0.945", "0.668", "0.782", "334"],
        ["Tomato Septoria leaf spot", "0.799", "0.890", "0.842", "335"],
    ])

    p("Table 4.3: Effect of the Confidence Threshold", size=10, italic=True, space_before=14, space_after=4)
    t_43 = doc.add_table(rows=1, cols=3)
    format_table(t_43, [Cm(4.0), Cm(5.5), Cm(5.5)],
                 ["Threshold", "Images Answered", "Accuracy on Answered"], [
        ["0.5", "98.0%", "95.7%"],
        ["0.6", "95.5%", "96.8%"],
        ["0.7 (used)", "92.9%", "97.6%"],
        ["0.8", "89.9%", "98.5%"],
        ["0.9", "85.2%", "99.2%"],
    ])

    p("Table 4.4: System Tests", size=10, italic=True, space_before=14, space_after=4)
    t_44 = doc.add_table(rows=1, cols=3)
    format_table(t_44, [Cm(5.0), Cm(7.0), Cm(3.0)],
                 ["Test Function", "Tested Scenario", "Status"], [
        ["test_health", "Liveness probe returns 200 OK", "Passed"],
        ["test_classes_lists_38", "38 class labels enumerated", "Passed"],
        ["test_register_and_duplicate", "Duplicate user 409 conflict", "Passed"],
        ["test_register_validation", "Password minimum length (422)", "Passed"],
        ["test_login_wrong_password", "Wrong credential 401 check", "Passed"],
        ["test_me_requires_valid_token", "JWT authorization guard", "Passed"],
        ["test_predict_requires_login", "Unauthenticated upload block", "Passed"],
        ["test_predict_crud_flow", "End-to-end diagnosis and CRUD", "Passed"],
        ["test_user_isolation", "Cross-tenant record isolation", "Passed"],
    ])
    p("Result: 11 of 11 tests passed.", bold=True, space_before=6)

    section_heading("4.3 Analysis of Results")
    p("The model separates most classes very well, with 14-crop coverage. Errors concentrate in the tomato block: Early blight "
      "is often confused with Septoria, Target Spot, and Bacterial spot, all of which produce brown leaf spots. Tomato healthy "
      "has high recall (0.99) but lower precision (0.82), which means some diseased leaves are predicted healthy, the more costly error. "
      "Accuracy rises steadily with the threshold, which shows that confidence carries information; our 0.70 setting trades about 7% "
      "coverage for about 3 points of accuracy. Quantisation cost about 0.35 percentage points (95.06% to 94.71%) in exchange for a "
      "much smaller, faster model (2.57 MB).")

    section_heading("4.4 Comparison with Existing Methods")
    p("These are authors\u2019 reported figures on different data and splits, so they are not directly comparable.")
    p("Table 4.5: Comparison with Published Methods", size=10, italic=True, space_before=6, space_after=4)
    t_comp = doc.add_table(rows=1, cols=3)
    format_table(t_comp, [Cm(4.0), Cm(6.0), Cm(5.0)],
                 ["Work", "Approach", "Reported Result"], [
        ["Mohanty et al. (2016)", "CNN on PlantVillage", "Very high on lab images, ~31% on different sources"],
        ["This project", "Frozen MobileNetV2 + quantised TFLite", "94.71% on held-out lab images (97.6% calibrated)"],
    ])
    p("Our accuracy is lower than the best published lab results because we train only a small head on a frozen small network, "
      "by design, to keep the model light enough for a low-cost server. Our contribution is the secured, deployed service around the model.")

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 5: INFERENCES
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(5, "Inferences")

    section_heading("5.1 Key Findings")
    p("1. A frozen MobileNetV2 with a small trained head reaches 94.7% on 38 classes with a model that runs in about 20 ms.")
    p("2. Rejecting low-confidence predictions improves reliability at a small cost in coverage.")
    p("3. Tomato leaf-spot diseases are the main source of error.")
    p("4. Graceful degradation kept the service available when our first LLM provider denied access.")
    p("5. The service can run on low-cost cloud resources with HTTPS, authentication, and monitoring.")

    section_heading("5.2 Interpretation of Results")
    p("The confusion pattern matches what is visible to the eye: several diseases differ mainly in the pattern of brown spots, "
      "and a frozen general-purpose feature extractor has limited ability to separate them. Fine-tuning the base network and adding "
      "field photographs should help. The high lab accuracy should not be read as field accuracy, because PlantVillage images have "
      "uniform backgrounds, and several photos of one leaf may appear on both sides of the split.")

    section_heading("5.3 Implications of the Study")
    p("1. A small team can offer AI diagnosis as a web service with a modest cloud budget.")
    p("2. The LLM-plus-fallback pattern is a general way to use an unreliable third-party service safely.")
    p("3. Service-model trade-off: EC2 (IaaS) gives full control and keeps a local database, at the cost of managing the operating "
      "system and process. A serverless (Lambda) design removes server management but would need a managed database, and a PaaS option "
      "would reduce operations further but gives less control over the runtime.")

    section_heading("5.4 Fulfillment of Objectives")
    p("Each objective is proved by statistical methods as required:", bold=True, space_after=8)
    p("Table 5.1: Statistical Hypothesis Verification of Stated Objectives", size=10, italic=True, space_before=4, space_after=4)
    t_obj = doc.add_table(rows=1, cols=4)
    format_table(t_obj, [Cm(3.5), Cm(3.0), Cm(3.5), Cm(5.0)],
                 ["Objective", "Target", "Result", "Statistical Evidence"], [
        ["1. Accuracy", "\u2265 90%", "94.71%",
         "95% CI 94.28 to 95.13 (n = 10,861; lower bound > 90%, p < 0.0001)."],
        ["2. Inference Time", "< 100 ms", "Mean 20.5 ms (p95 28.0 ms)",
         "n = 10,861 CPU executions; satisfies target by 3.5\u00d7 margin."],
        ["3. Reliability", "\u2265 95%", "97.6% on 92.9% images",
         "Approximate 95% CI 97.3 to 97.9 (n \u2248 10,090 answered)."],
        ["4. Secure CRUD", "All tests pass", "11 of 11 passed",
         "Automated pytest verification suite."],
        ["5. Cloud Deploy", "Deployed & monitored", "Live on AWS",
         "Deployed on EC2, S3, CloudFront, IAM, CloudWatch."],
    ])
    p("Method: Binomial proportion confidence intervals (normal approximation; the Wilson interval, Wilson 1927, "
      "is suitable for small samples). Accuracy, precision, recall, and F1 are computed directly from the confusion matrix.",
      space_before=8)

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 6: CONCLUSION
    # ══════════════════════════════════════════════════════════════════════════
    chapter_heading(6, "Conclusion")

    section_heading("6.1 Results")
    p("The project delivers a working, secured, cloud-deployed REST service that identifies 38 plant diseases at 94.7% validation "
      "accuracy, rejects uncertain inputs, explains diagnoses, and keeps each user\u2019s history privately. All five objectives were "
      "evaluated and met on statistical evidence.")
    p("Limitations: Only 38 PlantVillage classes; lab-image bias; some diseased tomato leaves predicted healthy; LLM text may "
      "vary or be wrong, so it is accompanied by a disclaimer; the demo server\u2019s API port is open and CORS is permissive.")

    section_heading("6.2 Future Work")
    p("1. Retrieval-augmented explanations grounded in agricultural documents, with citations (Lewis et al., 2020).")
    p("2. Fine-tune the base network and add field-collected images.")
    p("3. Containerise the service with Docker, and restrict network access so only CloudFront reaches the server.")
    p("4. Per-class thresholds and probability calibration.")
    p("5. Support more crops and regional languages.")

    section_heading("6.3 References")
    refs = [
        "Amazon Web Services. (2026). AWS documentation (EC2, S3, CloudFront, IAM, CloudWatch). https://docs.aws.amazon.com",
        "Barbedo, J. G. A. (2018). Impact of dataset size and variety on the effectiveness of deep learning and transfer learning for plant disease classification. Computers and Electronics in Agriculture, 153, 46\u201353.",
        "Chow, C. K. (1970). On optimum recognition error and reject tradeoff. IEEE Transactions on Information Theory, 16(1), 41\u201346.",
        "Ferentinos, K. P. (2018). Deep learning models for plant disease detection and diagnosis. Computers and Electronics in Agriculture, 145, 311\u2013318.",
        "Fielding, R. T. (2000). Architectural styles and the design of network-based software architectures [Doctoral dissertation, University of California, Irvine].",
        "Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. Proceedings of ICML, 70, 1321\u20131330.",
        "Hughes, D. P., & Salath\u00e9, M. (2015). An open access repository of images on plant health to enable the development of mobile disease diagnostics. arXiv:1511.08060.",
        "Jacob, B., et al. (2018). Quantization and training of neural networks for efficient integer-arithmetic-only inference. Proceedings of CVPR, 2704\u20132713.",
        "Ji, Z., et al. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), 1\u201338.",
        "Jones, M., Bradley, J., & Sakimura, N. (2015). JSON Web Token (JWT) (RFC 7519). IETF.",
        "Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459\u20139474.",
        "Mell, P., & Grance, T. (2011). The NIST definition of cloud computing (SP 800-145). NIST.",
        "Mohanty, S. P., Hughes, D. P., & Salath\u00e9, M. (2016). Using deep learning for image-based plant disease detection. Frontiers in Plant Science, 7, 1419.",
        "Pan, S. J., & Yang, Q. (2010). A survey on transfer learning. IEEE Transactions on Knowledge and Data Engineering, 22(10), 1345\u20131359.",
        "Provos, N., & Mazi\u00e8res, D. (1999). A future-adaptable password scheme. Proceedings of USENIX Annual Technical Conference, 81\u201391.",
        "Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L.-C. (2018). MobileNetV2: Inverted residuals and linear bottlenecks. Proceedings of CVPR, 4510\u20134520.",
        "Vaswani, A., et al. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998\u20136008.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209\u2013212.",
    ]
    for r in refs:
        pa = p(r, space_after=4)
        pa.paragraph_format.left_indent = Inches(0.5)
        pa.paragraph_format.first_line_indent = Inches(-0.5)

    # ══════════════════════════════════════════════════════════════════════════
    # APPENDIX
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_page_break()
    p("APPENDIX", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_before=18, space_after=18)
    p("A. Key source code listings (app.py, auth.py, predict.py, explain.py, database.py, models.py).")
    p("B. Full API reference with sample requests, response schemas, and OpenAPI endpoints.")
    p("C. Screenshots index: Swagger /docs, CRUD in action, \u2018uncertain\u2019 threshold alert, SQLite tables, 401/404 security checks, Pytest 11/11 output, S3 buckets, CloudFront behaviors, IAM role, EC2 instance, CloudWatch metrics.")
    p("D. Environment variables table (.env) and deployment configuration.")
    p("E. Full per-class precision/recall/F1 table and confusion matrix analysis.")

    # ── Ensure page numbers on all sections ──
    for sec in doc.sections:
        add_page_number_footer(sec)

    # ── Save ──
    out1 = "F:/plant-disease-advisor/Plant_Disease_Advisor_Project_Report.docx"
    out2 = "C:/Users/Lenovo/Downloads/Plant_Disease_Advisor_Project_Report.docx"
    out3 = "C:/Users/Lenovo/OneDrive/Desktop/Plant_Disease_Advisor_Project_Report.docx"
    doc.save(out1)
    try:
        doc.save(out2)
    except Exception:
        doc.save("C:/Users/Lenovo/Downloads/Plant_Disease_Advisor_Report_v2.docx")
    try:
        doc.save(out3)
    except Exception:
        doc.save("C:/Users/Lenovo/OneDrive/Desktop/Plant_Disease_Advisor_Report_v2.docx")
    print("Report generated successfully!")

if __name__ == "__main__":
    generate_rvu_report()
