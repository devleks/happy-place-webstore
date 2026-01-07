# Email Setup Guide - SMTP Configuration

**Last Updated:** January 3, 2026
**Purpose:** Configure email notifications using your own website's email server

---

## ✅ What We Need

To send order confirmations, shipping notifications, and other transactional emails, you need to configure SMTP settings from your website's email server.

---

## 📋 Required Information

You'll need the following details from your website hosting provider or email service:

### 1. SMTP Server Details
- **SMTP Host:** The mail server address (e.g., `smtp.yourwebsite.com`, `mail.yourwebsite.com`)
- **SMTP Port:** Usually one of these:
  - `587` (TLS/STARTTLS - recommended)
  - `465` (SSL)
  - `25` (Unencrypted - not recommended)

### 2. Authentication
- **Username:** Usually your full email address (e.g., `noreply@yourwebsite.com`)
- **Password:** Your email account password or app-specific password

### 3. Email Sender Information
- **From Email:** The sender address (e.g., `noreply@happyplace.com`)
- **From Name:** Display name (e.g., `Happy Place Boutique`)
- **Reply-To Email:** Where customers can reply (e.g., `support@happyplace.com`)

---

## 🔧 Configuration Steps

### Step 1: Find Your SMTP Settings

**Common hosting providers:**

| Provider | SMTP Host | Port | TLS |
|----------|-----------|------|-----|
| **cPanel** | mail.yourdomain.com | 587 | Yes |
| **Plesk** | smtp.yourdomain.com | 587 | Yes |
| **Gmail** | smtp.gmail.com | 587 | Yes |
| **Outlook/Office 365** | smtp.office365.com | 587 | Yes |
| **Custom Server** | Ask your hosting provider | - | - |

**How to find your settings:**
1. Log into your website hosting control panel (cPanel, Plesk, etc.)
2. Look for "Email Accounts" or "Email Configuration"
3. Find SMTP/Outgoing Mail Server settings
4. Note down the host, port, and authentication details

### Step 2: Update `.env` File

Open `backend/.env` and update these lines (around line 41-57):

```bash
# Email Configuration (SMTP)
EMAIL_ENABLED=true
SMTP_HOST=smtp.yourwebsite.com          # ← Your SMTP host
SMTP_PORT=587                            # ← Your SMTP port
SMTP_USE_TLS=true                        # ← true for port 587, false for 465
SMTP_USE_SSL=false                       # ← true for port 465, false for 587
SMTP_USERNAME=noreply@yourwebsite.com    # ← Your email username
SMTP_PASSWORD=your-email-password        # ← Your email password

# Email sender details
EMAIL_FROM=noreply@happyplace.com        # ← Sender email
EMAIL_FROM_NAME=Happy Place Boutique     # ← Sender name
EMAIL_REPLY_TO=support@happyplace.com    # ← Reply-to email

# Website URL (for email links)
WEBSITE_URL=https://happyplace.com       # ← Your website URL
```

### Step 3: Test Email Configuration

Run the test script to verify everything works:

```bash
cd backend
python test_email.py
```

The test will:
1. ✅ Test SMTP connection and authentication
2. ✅ Send a simple test email
3. ✅ Send order confirmation email (with sample data)
4. ✅ Send shipping notification email (with sample data)

**You'll be prompted to enter your email address to receive test emails.**

---

## 🔒 Security Notes

### For Gmail Users

If using Gmail SMTP, you need to:
1. Enable 2-factor authentication
2. Generate an "App Password" (don't use your regular Gmail password)
3. Use the app password in `.env`

**Steps:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and generate password
5. Use the 16-character password in `SMTP_PASSWORD`

### For Custom Email Servers

- **Never commit passwords to git** - `.env` is already in `.gitignore`
- Use strong passwords for email accounts
- Consider creating a dedicated `noreply@` or `orders@` email account
- Enable TLS/SSL encryption (port 587 or 465)

---

## 📧 Email Templates Included

### 1. Order Confirmation
Sent when customer places an order.

**Includes:**
- Order number and date
- Itemized product list with quantities and prices
- Total amount
- Payment method
- Shipping address
- Link to view order details

### 2. Shipping Notification
Sent when order is shipped.

**Includes:**
- Tracking number
- Carrier name
- Estimated delivery date
- Link to track package

### 3. Delivery Confirmation
Sent when order is delivered.

**Includes:**
- Delivery date
- Link to write product review
- Thank you message

### 4. Password Reset
Sent when customer requests password reset.

**Includes:**
- Secure reset link (expires in 1 hour)
- Security warning
- Fallback link if button doesn't work

---

## 🧪 Testing Checklist

After configuring, verify these work:

- [ ] SMTP connection establishes successfully
- [ ] Test email delivers to inbox (not spam)
- [ ] Order confirmation email renders correctly
- [ ] Shipping notification email renders correctly
- [ ] Email links work (view order, track package)
- [ ] Reply-to address is correct
- [ ] Emails are not marked as spam

**Tip:** Test with multiple email providers (Gmail, Outlook, Yahoo) to ensure compatibility.

---

## 🐛 Troubleshooting

### Issue 1: "Authentication failed"
**Causes:**
- Wrong username or password
- Need app-specific password (Gmail, Yahoo)
- 2FA enabled but not using app password

**Fix:**
- Double-check credentials
- Generate app password if using Gmail/Yahoo
- Verify username is full email address

### Issue 2: "Connection timeout"
**Causes:**
- Wrong SMTP host or port
- Firewall blocking SMTP ports
- Server doesn't support TLS/SSL on that port

**Fix:**
- Verify SMTP host and port with hosting provider
- Try port 587 (TLS) or 465 (SSL)
- Check `SMTP_USE_TLS` and `SMTP_USE_SSL` settings match port

### Issue 3: "SMTP server not found"
**Causes:**
- Incorrect SMTP hostname
- DNS issue

**Fix:**
- Confirm SMTP host with hosting provider
- Try `ping smtp.yourwebsite.com` to verify DNS
- Use IP address instead of hostname temporarily

### Issue 4: Emails go to spam
**Causes:**
- Missing SPF/DKIM records
- From address doesn't match domain
- Content triggers spam filters

**Fix:**
- Ask hosting provider to configure SPF/DKIM
- Use email address from same domain as SMTP server
- Test with simple text email first

---

## 📊 SMTP Settings Examples

### Example 1: cPanel Email
```bash
SMTP_HOST=mail.yourwebsite.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=orders@yourwebsite.com
SMTP_PASSWORD=your-cpanel-email-password
```

### Example 2: Gmail (for testing only)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=youremail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### Example 3: Office 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=youremail@yourcompany.com
SMTP_PASSWORD=your-office365-password
```

---

## 🚀 Next Steps After Setup

Once emails are working:

1. **Wire email triggers** - Connect to order lifecycle events
2. **Test full flow** - Place test order and verify all emails send
3. **Customize templates** - Update branding, colors, store info
4. **Monitor delivery** - Check email logs for any failures
5. **Production deployment** - Update `WEBSITE_URL` for production links

---

## 📞 Need Help?

**Common Questions:**
- **Q: Can I use Gmail for production?**
  A: Not recommended. Gmail has daily send limits (100-500/day). Use a professional email service.

- **Q: What if my hosting doesn't have SMTP?**
  A: Contact your hosting provider - most include email. Or use SendGrid/Mailgun (modify `email_service.py`).

- **Q: How do I change email templates?**
  A: Edit methods in `backend/services/email_service.py` (lines 300+)

- **Q: Can I test without a real SMTP server?**
  A: Yes! Set `EMAIL_ENABLED=false` in `.env` - emails will be logged but not sent.

---

**Documentation:** `backend/services/email_service.py` (570 lines)
**Test Script:** `backend/test_email.py`
**Environment Variables:** `backend/.env` (lines 41-57)
