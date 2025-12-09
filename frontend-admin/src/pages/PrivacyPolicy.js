import React from 'react';
import '../styles/PolicyPages.css';

const PrivacyPolicy = () => {
  return (
    <div className="policy-page">
      <div className="policy-container">
        <h1 className="policy-title">Privacy Policy</h1>
        <p className="policy-updated">Last Updated: November 26, 2025</p>

        <div className="policy-content">
          <section className="policy-section">
            <h2>1. Introduction</h2>
            <p>
              Welcome to Happy Place Boutique ("we," "our," or "us"). We are committed to protecting your personal 
              information and your right to privacy. This Privacy Policy explains how we collect, use, disclose, 
              and safeguard your information when you visit our website and make purchases.
            </p>
            <p>
              By using our website, you agree to the collection and use of information in accordance with this policy.
            </p>
          </section>

          <section className="policy-section">
            <h2>2. Information We Collect</h2>
            
            <h3>2.1 Personal Information</h3>
            <p>When you create an account or place an order, we collect:</p>
            <ul>
              <li>Full name (first and last name)</li>
              <li>Email address</li>
              <li>Phone number</li>
              <li>Delivery address (street, city, state, postal code)</li>
              <li>Billing address (if different from delivery address)</li>
            </ul>

            <h3>2.2 Payment Information</h3>
            <p>For Cash on Delivery orders:</p>
            <ul>
              <li>We do not collect or store credit card information</li>
              <li>Payment is collected at the time of delivery</li>
            </ul>
            <p>For M-Pesa payments (when available):</p>
            <ul>
              <li>M-Pesa phone number</li>
              <li>Transaction reference numbers</li>
            </ul>

            <h3>2.3 Order Information</h3>
            <ul>
              <li>Products purchased</li>
              <li>Order value and shipping costs</li>
              <li>Order history and status</li>
            </ul>

            <h3>2.4 Automatically Collected Information</h3>
            <ul>
              <li>IP address</li>
              <li>Browser type and version</li>
              <li>Device information</li>
              <li>Pages visited and time spent on site</li>
            </ul>
          </section>

          <section className="policy-section">
            <h2>3. How We Use Your Information</h2>
            <p>We use your personal information to:</p>
            <ul>
              <li>Process and fulfill your orders</li>
              <li>Send order confirmations and shipping notifications</li>
              <li>Respond to your inquiries and customer service requests</li>
              <li>Improve our products and website experience</li>
              <li>Send promotional emails about new products and special offers (with your consent)</li>
              <li>Prevent fraud and ensure website security</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="policy-section">
            <h2>4. Data Security</h2>
            <p>
              We take your privacy seriously and implement industry-standard security measures to protect your 
              personal information:
            </p>
            <ul>
              <li><strong>Encryption:</strong> All personal data is encrypted at rest using AES-256 encryption</li>
              <li><strong>Secure Transmission:</strong> Data transmitted over the internet uses HTTPS encryption</li>
              <li><strong>Access Controls:</strong> Only authorized personnel have access to customer data</li>
              <li><strong>Regular Audits:</strong> We conduct regular security audits and updates</li>
            </ul>
            <p>
              However, no method of transmission over the internet is 100% secure. While we strive to protect 
              your personal information, we cannot guarantee its absolute security.
            </p>
          </section>

          <section className="policy-section">
            <h2>5. Data Sharing and Disclosure</h2>
            
            <h3>5.1 We DO NOT Sell Your Data</h3>
            <p>
              We do not sell, rent, or trade your personal information to third parties for marketing purposes.
            </p>

            <h3>5.2 We Share Data With:</h3>
            <ul>
              <li><strong>Delivery Partners:</strong> To fulfill and deliver your orders (name, address, phone)</li>
              <li><strong>Payment Processors:</strong> To process M-Pesa payments (when applicable)</li>
              <li><strong>Legal Authorities:</strong> When required by law or to protect our rights</li>
            </ul>
          </section>

          <section className="policy-section">
            <h2>6. Your Privacy Rights</h2>
            <p>Under Kenyan data protection laws, you have the right to:</p>
            <ul>
              <li><strong>Access:</strong> Request a copy of the personal data we hold about you</li>
              <li><strong>Correction:</strong> Request correction of inaccurate or incomplete data</li>
              <li><strong>Deletion:</strong> Request deletion of your personal data (right to be forgotten)</li>
              <li><strong>Portability:</strong> Request transfer of your data to another service</li>
              <li><strong>Withdraw Consent:</strong> Opt-out of marketing communications at any time</li>
              <li><strong>Object:</strong> Object to processing of your personal data</li>
            </ul>
            <p>
              To exercise any of these rights, please contact us at privacy@happyplace.co.ke or call 
              +254 712 345 678.
            </p>
          </section>

          <section className="policy-section">
            <h2>7. Data Retention</h2>
            <p>We retain your personal information for as long as necessary to:</p>
            <ul>
              <li>Fulfill orders and provide customer service</li>
              <li>Comply with legal, tax, and accounting obligations (typically 7 years)</li>
              <li>Resolve disputes and enforce our agreements</li>
            </ul>
            <p>
              Inactive accounts (no purchases or logins for 3 years) will be anonymized, with personal 
              identifiers removed while retaining order history for business records.
            </p>
          </section>

          <section className="policy-section">
            <h2>8. Cookies and Tracking</h2>
            <p>We use cookies and similar technologies to:</p>
            <ul>
              <li>Keep you logged in to your account</li>
              <li>Remember items in your shopping cart</li>
              <li>Analyze website traffic and user behavior</li>
              <li>Personalize your shopping experience</li>
            </ul>
            <p>
              You can control cookies through your browser settings. However, disabling cookies may limit 
              your ability to use certain features of our website.
            </p>
          </section>

          <section className="policy-section">
            <h2>9. Children's Privacy</h2>
            <p>
              Our website is not intended for children under 18 years of age. We do not knowingly collect 
              personal information from children. If you believe we have collected information from a child, 
              please contact us immediately.
            </p>
          </section>

          <section className="policy-section">
            <h2>10. Marketing Communications</h2>
            <p>
              With your consent, we may send you promotional emails about:
            </p>
            <ul>
              <li>New product arrivals</li>
              <li>Special offers and discounts</li>
              <li>Exclusive sales events</li>
            </ul>
            <p>
              You can unsubscribe from marketing emails at any time by clicking the "unsubscribe" link at 
              the bottom of any promotional email, or by contacting us directly.
            </p>
          </section>

          <section className="policy-section">
            <h2>11. Changes to This Privacy Policy</h2>
            <p>
              We may update this Privacy Policy from time to time to reflect changes in our practices or 
              legal requirements. We will notify you of any material changes by:
            </p>
            <ul>
              <li>Posting the updated policy on our website</li>
              <li>Updating the "Last Updated" date</li>
              <li>Sending an email notification for significant changes</li>
            </ul>
            <p>
              Your continued use of our website after any changes constitutes acceptance of the updated policy.
            </p>
          </section>

          <section className="policy-section">
            <h2>12. Contact Us</h2>
            <p>
              If you have questions, concerns, or requests regarding this Privacy Policy or our data practices, 
              please contact us:
            </p>
            <div className="contact-info">
              <p><strong>Happy Place Boutique</strong></p>
              <p>Email: privacy@happyplace.co.ke</p>
              <p>Phone: +254 712 345 678</p>
              <p>Address: Westlands, Nairobi, Kenya</p>
            </div>
          </section>

          <section className="policy-section">
            <h2>13. Governing Law</h2>
            <p>
              This Privacy Policy is governed by and construed in accordance with the laws of Kenya, including 
              the Data Protection Act, 2019. Any disputes arising from this policy shall be subject to the 
              exclusive jurisdiction of Kenyan courts.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
