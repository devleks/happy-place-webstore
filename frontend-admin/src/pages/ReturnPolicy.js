import React from 'react';
import '../styles/PolicyPages.css';

const ReturnPolicy = () => {
  return (
    <div className="policy-page">
      <div className="policy-container">
        <h1 className="policy-title">Return & Refund Policy</h1>
        <p className="policy-updated">Last Updated: November 26, 2025</p>

        <div className="policy-content">
          <section className="policy-section">
            <h2>1. Overview</h2>
            <p>
              At Happy Place Boutique, we want you to love your purchase. However, we understand that sometimes 
              items may not meet your expectations. This Return & Refund Policy outlines the conditions under 
              which returns and refunds are accepted.
            </p>
            <p className="important-notice">
              <strong>Important:</strong> Please read this policy carefully before making a purchase, as certain 
              items are not eligible for returns.
            </p>
          </section>

          <section className="policy-section">
            <h2>2. Return Eligibility</h2>
            
            <h3>2.1 Regular-Priced Items</h3>
            <div className="policy-highlight">
              <p><strong> RETURNS ACCEPTED</strong></p>
              <ul>
                <li>Regular-priced items may be returned within <strong>2 days from delivery</strong></li>
                <li>A <strong>10% restocking fee</strong> will be applied to the refund amount</li>
                <li>Items must meet all condition requirements (see Section 3)</li>
              </ul>
            </div>

            <h3>2.2 Sale and Clearance Items</h3>
            <div className="policy-highlight final-sale">
              <p><strong> FINAL SALE - NO RETURNS, NO EXCHANGES</strong></p>
              <ul>
                <li><strong>Sale items:</strong> Items purchased at a discounted price</li>
                <li><strong>Clearance items:</strong> Items marked as clearance</li>
                <li>These purchases are final and cannot be returned or exchanged</li>
                <li>All sales are final once the order is placed</li>
              </ul>
            </div>

            <h3>2.3 Return Window</h3>
            <p>
              Returns must be initiated within <strong>2 days from the delivery date</strong>. After this period, 
              we cannot accept returns, even for regular-priced items.
            </p>
            <p className="example">
              <strong>Example:</strong> If your order was delivered on Monday, you must request a return by 
              Wednesday (2 days later).
            </p>
          </section>

          <section className="policy-section">
            <h2>3. Item Condition Requirements</h2>
            <p>
              To be eligible for a return, items must meet ALL of the following conditions:
            </p>

            <h3>3.1 Unworn and Unused</h3>
            <ul>
              <li>Items must be unworn and unused</li>
              <li>No signs of wear, washing, or alteration</li>
              <li>Must be in the same condition as received</li>
            </ul>

            <h3>3.2 Original Packaging</h3>
            <ul>
              <li>Items must be in original packaging (if applicable)</li>
              <li>All original tags must be attached and intact</li>
              <li>Labels must not be torn, removed, or damaged</li>
            </ul>

            <h3>3.3 NOT ACCEPTABLE for Returns</h3>
            <div className="policy-highlight not-acceptable">
              <p><strong>We CANNOT accept returns for:</strong></p>
              <ul>
                <li> Used products (worn, washed, or altered items)</li>
                <li> Products with torn or removed labels</li>
                <li> Damaged products (unless damage occurred during shipping - see Section 7)</li>
                <li> Products showing signs of wear or use</li>
                <li> Products that have been washed or dry-cleaned</li>
                <li> Sale or clearance items (FINAL SALE)</li>
              </ul>
            </div>
          </section>

          <section className="policy-section">
            <h2>4. Restocking Fee</h2>
            <p>
              A <strong>10% restocking fee</strong> applies to all eligible returns of regular-priced items.
            </p>
            <p className="example">
              <strong>Example:</strong>
              <br />
              Original purchase price: KSh 3,000
              <br />
              Restocking fee (10%): KSh 300
              <br />
              Refund amount: KSh 2,700
            </p>
            <p>
              The restocking fee covers the cost of processing the return, inspecting the item, and restocking 
              it for resale.
            </p>
          </section>

          <section className="policy-section">
            <h2>5. How to Initiate a Return</h2>
            
            <h3>Step 1: Contact Customer Service</h3>
            <p>Within 2 days of delivery, contact us via:</p>
            <ul>
              <li>Email: returns@happyplace.co.ke</li>
              <li>Phone: +254 712 345 678</li>
              <li>WhatsApp: +254 712 345 678</li>
            </ul>
            <p>Provide the following information:</p>
            <ul>
              <li>Order number</li>
              <li>Item(s) you wish to return</li>
              <li>Reason for return</li>
              <li>Photos of the item (if applicable)</li>
            </ul>

            <h3>Step 2: Return Authorization</h3>
            <p>
              Our team will review your request and issue a Return Authorization Number (RMA) if your return 
              is approved. <strong>Do not send items back without an RMA number.</strong>
            </p>

            <h3>Step 3: Ship the Item</h3>
            <p>
              Package the item securely in its original packaging with all tags attached. Include a copy of 
              your order confirmation and the RMA number.
            </p>
            <p>
              <strong>Return Shipping:</strong> Customer is responsible for return shipping costs unless the 
              item was defective or damaged during shipping.
            </p>

            <h3>Step 4: Inspection and Refund</h3>
            <p>
              Once we receive your return, we will inspect the item within 3-5 business days. If approved, 
              your refund will be processed as follows:
            </p>
            <ul>
              <li><strong>COD orders:</strong> Refund via M-Pesa or bank transfer (minus restocking fee)</li>
              <li><strong>M-Pesa orders:</strong> Refund to original M-Pesa number (minus restocking fee)</li>
            </ul>
            <p>
              Refunds typically take 5-10 business days to appear in your account.
            </p>
          </section>

          <section className="policy-section">
            <h2>6. Exchanges</h2>
            <p>
              We do not offer direct exchanges. If you need a different size or color:
            </p>
            <ol>
              <li>Return the original item following the return process</li>
              <li>Place a new order for the desired item</li>
            </ol>
            <p>
              <strong>Exception:</strong> For defective or damaged items, we will offer a direct exchange 
              without additional charges (see Section 7).
            </p>
          </section>

          <section className="policy-section">
            <h2>7. Defective or Damaged Items</h2>
            <p>
              If you receive an item that is defective or damaged during shipping:
            </p>

            <h3>7.1 Immediate Action Required</h3>
            <ul>
              <li>Contact us within <strong>24 hours of delivery</strong></li>
              <li>Provide photos of the defect or damage</li>
              <li>Include photos of the packaging (if damaged in transit)</li>
            </ul>

            <h3>7.2 Resolution Options</h3>
            <p>For defective or damaged items, we will offer:</p>
            <ul>
              <li><strong>Replacement:</strong> We will send a new item at no charge</li>
              <li><strong>Full Refund:</strong> 100% refund with no restocking fee</li>
            </ul>
            <p>
              We will also cover return shipping costs for defective or damaged items.
            </p>
          </section>

          <section className="policy-section">
            <h2>8. Non-Returnable Items</h2>
            <p>The following items cannot be returned under any circumstances:</p>
            <ul>
              <li>Intimate apparel and undergarments (for hygiene reasons)</li>
              <li>Swimwear (unless tags are still attached and hygiene seal is intact)</li>
              <li>Gift cards</li>
              <li>Sale and clearance items (FINAL SALE)</li>
              <li>Items without original tags or packaging</li>
              <li>Items showing signs of wear or use</li>
            </ul>
          </section>

          <section className="policy-section">
            <h2>9. Refund Methods</h2>
            
            <h3>9.1 Cash on Delivery (COD) Orders</h3>
            <p>Refunds will be issued via:</p>
            <ul>
              <li><strong>M-Pesa:</strong> Direct transfer to your M-Pesa number</li>
              <li><strong>Bank Transfer:</strong> Transfer to your bank account (please provide account details)</li>
            </ul>

            <h3>9.2 M-Pesa Orders</h3>
            <p>
              Refunds will be sent to the original M-Pesa phone number used for payment.
            </p>

            <h3>9.3 Processing Time</h3>
            <ul>
              <li>Inspection: 3-5 business days after we receive the item</li>
              <li>Refund processing: 2-3 business days after approval</li>
              <li>Total time: 5-10 business days from receipt of returned item</li>
            </ul>
          </section>

          <section className="policy-section">
            <h2>10. Important Notes</h2>
            <div className="important-notice">
              <ul>
                <li>
                  <strong>Final Sale Items:</strong> All sale and clearance items are FINAL SALE. No returns, 
                  no exchanges, no exceptions (unless defective).
                </li>
                <li>
                  <strong>Restocking Fee:</strong> 10% restocking fee applies to all eligible returns of 
                  regular-priced items.
                </li>
                <li>
                  <strong>Return Window:</strong> 2 days from delivery for regular-priced items only.
                </li>
                <li>
                  <strong>Condition Matters:</strong> Items must be unworn, unwashed, and with original tags 
                  attached.
                </li>
                <li>
                  <strong>No Direct Exchanges:</strong> Return the item and place a new order for a different 
                  size/color.
                </li>
              </ul>
            </div>
          </section>

          <section className="policy-section">
            <h2>11. Customer Service</h2>
            <p>
              We are here to help! If you have questions about our return policy or need assistance with a 
              return, please contact us:
            </p>
            <div className="contact-info">
              <p><strong>Happy Place Boutique Returns Department</strong></p>
              <p>Email: returns@happyplace.co.ke</p>
              <p>Phone: +254 712 345 678</p>
              <p>WhatsApp: +254 712 345 678</p>
              <p>Hours: Monday-Saturday, 9:00 AM - 6:00 PM EAT</p>
            </div>
          </section>

          <section className="policy-section">
            <h2>12. Changes to This Policy</h2>
            <p>
              We reserve the right to update this Return & Refund Policy at any time. Changes will be effective 
              immediately upon posting on our website. Please review this policy before making a purchase.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default ReturnPolicy;
