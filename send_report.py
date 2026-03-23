#!/usr/bin/env python3
"""
生成紫光股份分析报告 PDF 并通过 Gmail 发送
"""
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import textwrap

# Register Chinese fonts
_CN_FONT = "Helvetica"
_CN_FONT_BOLD = "Helvetica-Bold"
try:
    # Try PingFang SC (macOS built-in)
    pdfmetrics.registerFont(TTFont("PingFang", "/System/Library/Fonts/PingFang.ttc", subfontIndex=0))
    pdfmetrics.registerFont(TTFont("PingFangBold", "/System/Library/Fonts/PingFang.ttc", subfontIndex=1))
    _CN_FONT = "PingFang"
    _CN_FONT_BOLD = "PingFangBold"
except Exception:
    try:
        # Fallback: STHeiti
        pdfmetrics.registerFont(TTFont("STHeiti", "/System/Library/Fonts/STHeiti Medium.ttc", subfontIndex=0))
        _CN_FONT = "STHeiti"
        _CN_FONT_BOLD = "STHeiti"
    except Exception:
        try:
            # Fallback: CID font (no file needed)
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            _CN_FONT = "STSong-Light"
            _CN_FONT_BOLD = "STSong-Light"
        except Exception:
            pass  # Use Helvetica as last resort


SENDER_EMAIL = os.getenv("GMAIL_SENDER", "")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = "sliminem0410@gmail.com"
RESULTS_FILE = "/Users/luwenyu/TradingAgents/eval_results/000938.SZ/TradingAgentsStrategy_logs/full_states_log_2025-03-20.json"


def load_results():
    """加载分析结果"""
    if not os.path.exists(RESULTS_FILE):
        return None
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_thinking(text):
    """移除 thinking 字段，提取纯文本内容"""
    if not text:
        return ""
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict):
                if item.get("type") != "thinking":
                    parts.append(item.get("text", ""))
        return "\n".join(parts)
    if isinstance(text, str):
        # 尝试解析 JSON 列表字符串
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                parts = []
                for item in parsed:
                    if isinstance(item, dict) and item.get("type") != "thinking":
                        parts.append(item.get("text", ""))
                return "\n".join(parts)
        except (json.JSONDecodeError, TypeError):
            pass
    return str(text)


def wrap_text(text, width=80):
    """按宽度换行"""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            wrapped = textwrap.fill(paragraph, width=width)
            lines.append(wrapped)
        else:
            lines.append("")
    return "\n".join(lines)


def create_pdf(data, output_path):
    """生成 PDF 报告"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=_CN_FONT_BOLD,
        fontSize=20,
        textColor=colors.HexColor('#1a3c6e'),
        spaceAfter=20,
        alignment=1,  # 居中
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=_CN_FONT,
        fontSize=10,
        textColor=colors.gray,
        alignment=1,
        spaceAfter=30,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=_CN_FONT_BOLD,
        fontSize=14,
        textColor=colors.HexColor('#1a3c6e'),
        spaceBefore=15,
        spaceAfter=8,
        borderPadding=(0, 0, 3, 0),
        borderWidth=0,
        borderColor=colors.HexColor('#1a3c6e'),
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=_CN_FONT,
        fontSize=9,
        leading=13,
        spaceAfter=8,
    )
    decision_style = ParagraphStyle(
        'Decision',
        parent=styles['Heading1'],
        fontName=_CN_FONT_BOLD,
        fontSize=24,
        textColor=colors.HexColor('#c0392b'),
        alignment=1,
        spaceBefore=20,
        spaceAfter=20,
    )

    story = []

    # ===== 封面 =====
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("紫光股份 (000938.SZ)", title_style))
    story.append(Paragraph("AI 多智能体量化分析报告", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"分析日期: 2025-03-20", subtitle_style))
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Paragraph("TradingAgents Framework | Claude AI", subtitle_style))
    story.append(Spacer(1, 2*cm))

    # 摘要表格
    summary_data = [
        ["股票代码", "000938.SZ"],
        ["股票名称", "紫光股份"],
        ["交易所", "深圳证券交易所"],
        ["分析日期", "2025-03-20"],
        ["分析框架", "TradingAgents Multi-Agent"],
        ["LLM", "Claude Sonnet 4.5 + Haiku 4.5"],
        ["数据源", "AKShare (东方财富)"],
    ]
    t = Table(summary_data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a3c6e')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), _CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ===== 技术分析报告 =====
    story.append(Paragraph("一、技术分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    market = strip_thinking(data.get("market_report", ""))
    if market:
        # 提取摘要部分
        lines = market.split("\n")
        for line in lines[:80]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 基本面报告 =====
    story.append(Paragraph("二、基本面分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    fundamentals = strip_thinking(data.get("fundamentals_report", ""))
    if fundamentals:
        for line in fundamentals.split("\n")[:60]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 中文情绪报告 =====
    story.append(Paragraph("三、中文情绪分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    cn_sentiment = strip_thinking(data.get("cn_sentiment_report", ""))
    if cn_sentiment:
        for line in cn_sentiment.split("\n")[:40]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    else:
        story.append(Paragraph("（暂无数据）", body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 政策分析报告 =====
    story.append(Paragraph("四、政策分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    policy = strip_thinking(data.get("policy_report", ""))
    if policy:
        for line in policy.split("\n")[:40]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    else:
        story.append(Paragraph("（暂无数据）", body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 资金流报告 =====
    story.append(Paragraph("五、资金流向分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    fund_flow = strip_thinking(data.get("fund_flow_report", ""))
    if fund_flow:
        for line in fund_flow.split("\n")[:40]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    else:
        story.append(Paragraph("（暂无数据）", body_style))

    story.append(PageBreak())

    # ===== 新闻分析报告 =====
    story.append(Paragraph("六、新闻与宏观分析报告", heading_style))
    story.append(Spacer(1, 0.3*cm))
    news = strip_thinking(data.get("news_report", ""))
    if news:
        for line in news.split("\n")[:60]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 投资辩论 =====
    story.append(Paragraph("七、牛熊辩论与投资决策", heading_style))
    story.append(Spacer(1, 0.3*cm))
    debate_state = data.get("investment_debate_state", {})
    bull = debate_state.get("bull_history", "")
    bear = debate_state.get("bear_history", "")
    plan = data.get("investment_plan", "")
    if plan:
        plan_text = strip_thinking(plan)
        for line in plan_text.split("\n")[:30]:
            if line.strip():
                story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ===== 最终决策 =====
    story.append(Paragraph("八、最终交易决策", heading_style))
    story.append(Spacer(1, 0.5*cm))

    final_decision = strip_thinking(data.get("final_trade_decision", ""))
    if final_decision:
        # 提取决策关键词
        decision_lines = final_decision.split("\n")
        for line in decision_lines[:50]:
            if line.strip():
                # 高亮 BUY/SELL/HOLD
                if any(kw in line.upper() for kw in ["BUY", "SELL", "HOLD", "推荐", "决策", "建议", "结论"]):
                    decision_line_style = ParagraphStyle(
                        'DecisionLine',
                        parent=body_style,
                        fontSize=11,
                        textColor=colors.HexColor('#2c3e50'),
                        fontName=_CN_FONT_BOLD,
                    )
                    story.append(Paragraph(line, decision_line_style))
                else:
                    story.append(Paragraph(line, body_style))

    # ===== 风险辩论 =====
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("九、风险评估与最终审批", heading_style))
    story.append(Spacer(1, 0.3*cm))
    risk_state = data.get("risk_debate_state", {})
    risk_decision = risk_state.get("judge_decision", "")
    risk_text = strip_thinking(risk_decision) if risk_decision else ""
    if risk_text:
        for line in risk_text.split("\n")[:30]:
            if line.strip():
                story.append(Paragraph(line, body_style))

    # ===== 页脚声明 =====
    story.append(Spacer(1, 1*cm))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName=_CN_FONT,
        fontSize=7,
        textColor=colors.gray,
        alignment=1,
    )
    story.append(Paragraph(
        "⚠️ 免责声明：本报告由 AI 多智能体系统自动生成，仅供研究参考，不构成任何投资建议。",
        disclaimer_style
    ))
    story.append(Paragraph(
        "投资有风险，决策需谨慎。历史表现不代表未来收益。",
        disclaimer_style
    ))

    doc.build(story)
    print(f"PDF 已生成: {output_path}")


def send_email(pdf_path):
    """通过 Gmail 发送 PDF"""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("错误：未设置 GMAIL_SENDER 或 GMAIL_APP_PASSWORD 环境变量")
        return False

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"【AI分析报告】紫光股份 000938.SZ - {datetime.now().strftime('%Y-%m-%d')}"

    body = """
您好，

附件是紫光股份 (000938.SZ) 的 AI 多智能体量化分析报告。

报告包含：
• 技术分析
• 基本面分析
• 中文情绪分析
• 政策分析
• 资金流向分析
• 新闻与宏观分析
• 牛熊辩论与投资决策
• 风险评估与最终审批

⚠️ 免责声明：本报告由 TradingAgents AI 多智能体系统自动生成，
仅供研究参考，不构成任何投资建议。投资有风险，决策需谨慎。

---
TradingAgents Framework | Claude AI
"""

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 附加 PDF
    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=紫光股份_000938_SZ_分析报告.pdf')
        msg.attach(part)

    # 发送
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件已发送至 {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def main():
    print(f"[{datetime.now()}] 等待结果文件...")

    # 最多等待 30 分钟
    import time
    max_wait = 30 * 60
    waited = 0
    interval = 30  # 每 30 秒检查一次

    while waited < max_wait:
        if os.path.exists(RESULTS_FILE):
            print(f"结果文件已就绪，开始生成 PDF...")
            break
        time.sleep(interval)
        waited += interval
        print(f"  已等待 {waited}s，结果文件尚未生成，继续等待...")
    else:
        print(f"❌ 等待 {max_wait}s 后结果文件仍未生成")
        return

    data = load_results()
    if not data:
        print("❌ 无法加载结果文件")
        return

    pdf_path = "/tmp/紫光股份_000938_SZ_分析报告.pdf"
    create_pdf(data, pdf_path)
    send_email(pdf_path)


if __name__ == "__main__":
    main()
