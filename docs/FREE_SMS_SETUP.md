# 📱 Free Unlimited SMS Setup for Monica

Monica now supports **multiple SMS methods** including a **100% free unlimited option** using your phone carrier's email-to-SMS gateway!

---

## 🎯 Method 1: FREE UNLIMITED (Email-to-SMS Gateway)

### How It Works
Phone carriers provide free email-to-SMS gateways where emails sent to `YOURNUMBER@gateway.com` are delivered as SMS to your phone.

### Common Carrier Gateways

| Carrier | Email Gateway |
|---------|---------------|
| AT&T | `txt.att.net` |
| T-Mobile | `tmomail.net` |
| Verizon | `vtext.com` |
| Sprint | `messaging.sprintpcs.com` |
| US Cellular | `email.uscc.net` |
| Boost Mobile | `sms.myboostmobile.com` |
| Cricket | `sms.cricketwireless.net` |
| MetroPCS | `mymetropcs.com` |

### Setup Steps

1. **Find your carrier's gateway** from the table above

2. **Configure Monica**:
```python
# In your launch script or monica_interface.py
monica = MonicaCompleteInterface(phone_number="8134266783")

# Add email gateway to communication system
monica.communication.email_gateway = "txt.att.net"  # Change to your carrier
```

3. **Test it**:
```python
# Send free SMS
monica.communication.send_sms("Hello from Monica!", method='email')
```

### Important Notes
- ✅ **UNLIMITED** - No daily limits, completely free
- ⚠️ Requires local SMTP server OR Gmail with app password
- 📧 Messages come from an email address (not a phone number)
- ⏱️ May have 1-5 minute delay vs instant SMS

### Setting Up Gmail SMTP (for email method)

If you don't have a local SMTP server, use Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Create App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Create password for "Mail"
   - Copy the 16-character password

3. **Update Monica's `_send_sms_via_email()` method**:
```python
def _send_sms_via_email(self, message: str, urgent: bool) -> Dict:
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        phone_digits = ''.join(filter(str.isdigit, self.phone_number))
        to_address = f"{phone_digits}@{self.email_gateway}"
        
        full_message = f"[MONICA AI] {message}"
        if urgent:
            full_message = f"URGENT: {full_message}"
        
        msg = MIMEText(full_message)
        msg['Subject'] = 'Monica AI'
        msg['From'] = 'your.email@gmail.com'  # ← YOUR GMAIL
        msg['To'] = to_address
        
        # Use Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your.email@gmail.com', 'your-app-password')  # ← YOUR CREDENTIALS
            server.send_message(msg)
        
        result = {
            'status': 'sent',
            'method': 'email-gateway',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'urgent': urgent
        }
        self.sms_history.append(result)
        return result
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'message': message}
```

---

## 📤 Method 2: Textbelt (1 Free Per Day)

Already configured! Monica defaults to this if no email gateway set.

```python
monica.communication.send_sms("Message", method='textbelt')
```

- ✅ Simple, no configuration
- ❌ Limited to 1 message per day (testing)
- 💰 Paid plans available for more

---

## 💰 Method 3: Vonage/Twilio (Paid, Unlimited)

For professional use with instant delivery:

### Vonage Setup
1. Sign up at https://dashboard.nexmo.com/sign-up
2. Get free trial credits ($2 = ~50 SMS)
3. Get API credentials from dashboard
4. Install SDK:
```bash
pip install vonage
```

5. **Update Monica's `_send_sms_via_vonage()` method**:
```python
def _send_sms_via_vonage(self, message: str, urgent: bool) -> Dict:
    try:
        import vonage
        
        client = vonage.Client(
            key="YOUR_API_KEY",
            secret="YOUR_API_SECRET"
        )
        sms = vonage.Sms(client)
        
        response = sms.send_message({
            "from": "Monica AI",
            "to": self.phone_number,
            "text": f"[MONICA] {message}"
        })
        
        if response["messages"][0]["status"] == "0":
            result = {
                'status': 'sent',
                'method': 'vonage',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            self.sms_history.append(result)
            return result
        else:
            return {'status': 'error', 'error': response["messages"][0]["error-text"]}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'message': message}
```

6. Send via Vonage:
```python
monica.communication.send_sms("Message", method='vonage')
```

**Costs**: ~$0.04 per SMS (varies by country)

---

## 🎯 Recommended Setup

**For Personal Use (Free)**:
```python
monica.communication.email_gateway = "txt.att.net"  # Your carrier
monica.communication.send_sms("Testing!", method='email')
```

**For Professional Use (Paid)**:
```python
# Configure Vonage/Twilio once, then:
monica.communication.send_sms("Appointment reminder", method='vonage')
```

---

## 🧪 Quick Test

```python
# Test all methods
monica.communication.send_sms("Test 1: Textbelt", method='textbelt')  # 1/day free
monica.communication.send_sms("Test 2: Email Gateway", method='email')  # Unlimited free
monica.communication.send_sms("Test 3: Vonage", method='vonage')  # Paid
```

---

## 🎤 Voice Command Integration

Monica already has voice commands for messaging! Just say:
- "Monica, text me reminder to take medication"
- "Monica, send me an SMS about tomorrow's meeting"

The default method is `email` (free unlimited), but you can change it in the code.

---

## ❓ Troubleshooting

### Email method not working?
- ✅ Verify your carrier's gateway address
- ✅ Check phone number format (digits only)
- ✅ Configure Gmail SMTP if using Gmail
- ✅ Check spam folder on your phone

### Textbelt says "quota exceeded"?
- ⚠️ You've used your 1 free message today
- 💡 Switch to email method (unlimited free)
- 💰 Or purchase Textbelt credits

### Want instant delivery?
- 💰 Use Vonage/Twilio (paid but professional)
- 📧 Email method has 1-5 min delay
- 🚀 Paid services = instant delivery

---

## 🎨 Summary

| Method | Cost | Limit | Speed | Setup |
|--------|------|-------|-------|-------|
| **Email Gateway** | FREE | Unlimited | 1-5 min | Easy |
| **Textbelt** | FREE | 1/day | Instant | None |
| **Vonage** | $0.04/SMS | Unlimited | Instant | Medium |

**Best Choice**: Email gateway for free unlimited SMS! 🎉
