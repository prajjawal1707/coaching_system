import os
from io import BytesIO
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def money(value):
    return f"₹{int(value):,}"


def build_payment_receipt(payment, student):
    buffer = BytesIO()

    institute_name = os.getenv(
        "FEEFLOW_INSTITUTE_NAME",
        "FeeFlow Coaching Institute",
    )

    institute_address = os.getenv(
        "FEEFLOW_INSTITUTE_ADDRESS",
        "Address not configured",
    )

    gstin = os.getenv("FEEFLOW_GSTIN", "").strip()
    gst_rate_text = os.getenv("FEEFLOW_GST_RATE_PERCENT", "").strip()
    gst_inclusive = (
        os.getenv("FEEFLOW_GST_INCLUSIVE", "true").lower() == "true"
    )

    gst_configured = bool(gstin and gst_rate_text)

    gst_rate = Decimal("0")
    gst_amount = Decimal("0")
    taxable_amount = Decimal(str(payment.amount))

    if gst_configured:
        try:
            gst_rate = Decimal(gst_rate_text)
            if gst_rate < 0 or gst_rate > 100:
                raise ValueError("GST rate must be between 0 and 100.")
        except (InvalidOperation, ValueError):
            gst_configured = False
            gst_rate = Decimal("0")

    if gst_configured and gst_rate > 0:
        total = Decimal(str(payment.amount))

        if gst_inclusive:
            taxable_amount = (
                total / (Decimal("1") + gst_rate / Decimal("100"))
            )
            gst_amount = total - taxable_amount
        else:
            taxable_amount = total
            gst_amount = total * gst_rate / Decimal("100")

    receipt_number = f"FF-REC-{str(payment.id).replace('-', '').upper()}"

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReceiptTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=18,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallCenter",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RightText",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        )
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story = []

    story.append(Paragraph(escape(institute_name), styles["ReceiptTitle"]))
    story.append(
        Paragraph(escape(institute_address), styles["SmallCenter"])
    )
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("PAYMENT RECEIPT", styles["Heading1"]))
    story.append(Spacer(1, 4 * mm))

    payment_date = (
        payment.payment_date.strftime("%d-%m-%Y %I:%M %p")
        if payment.payment_date
        else "Not available"
    )

    details = [
        ["Receipt Number", receipt_number],
        ["Payment Date", payment_date],
        ["Student ID", student.id],
        ["Student Name", student.name],
        ["Course", student.course or "—"],
        ["Batch", student.batch or "—"],
        ["Payment Method", payment.payment_method or "—"],
        ["Transaction Reference", payment.transaction_reference or "—"],
        ["Payment Status", payment.status],
    ]

    details_table = Table(details, colWidths=[55 * mm, 105 * mm])
    details_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(details_table)
    story.append(Spacer(1, 8 * mm))

    if gst_configured:
        gst_rows = [
            ["Description", "Amount"],
            ["Payment amount", money(payment.amount)],
            ["Taxable value", money(taxable_amount)],
            [
                f"GST ({gst_rate}%)",
                money(gst_amount.quantize(Decimal("1"))),
            ],
            ["Total received", money(payment.amount if gst_inclusive else (
                Decimal(str(payment.amount)) + gst_amount
            ))],
            ["GSTIN", gstin],
        ]

        if not gst_inclusive:
            gst_rows.append([
                "Note",
                "GST is calculated separately from the payment amount.",
            ])
    else:
        gst_rows = [
            ["GST Details", "Pending institute configuration"],
            ["GSTIN", gstin or "Not provided"],
            ["GST rate", gst_rate_text or "Not provided"],
            [
                "Note",
                "This is a payment acknowledgement, not a tax invoice.",
            ],
        ]

    gst_table = Table(gst_rows, colWidths=[75 * mm, 85 * mm])
    gst_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ])
    )

    story.append(gst_table)
    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "This document confirms the payment recorded by FeeFlow. "
            "It is generated electronically and does not require a signature.",
            styles["SmallCenter"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer