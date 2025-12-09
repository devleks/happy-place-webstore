import React, { useState } from 'react';
import { getSizeGuideTable, REGION_LABELS } from '../utils/sizeConversion';
import '../styles/SizeGuide.css';

const SizeGuide = ({ selectedSize, onClose }) => {
  const [activeRegion, setActiveRegion] = useState('us');
  const sizeTable = getSizeGuideTable();

  const regions = ['us', 'uk', 'au', 'italy', 'france', 'germany', 'japan', 'russia'];

  return (
    <div className="size-guide-overlay" onClick={onClose}>
      <div className="size-guide-modal" onClick={(e) => e.stopPropagation()}>
        <div className="size-guide-header">
          <h2>International Size Guide</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="size-guide-tabs">
          {regions.map(region => (
            <button
              key={region}
              className={`size-tab ${activeRegion === region ? 'active' : ''}`}
              onClick={() => setActiveRegion(region)}
            >
              {REGION_LABELS[region]}
            </button>
          ))}
        </div>

        <div className="size-guide-content">
          <div className="size-guide-table-wrapper">
            <table className="size-guide-table">
              <thead>
                <tr>
                  <th>Size</th>
                  <th>US</th>
                  <th>UK/AU/NZ</th>
                  <th>Italy</th>
                  <th>France</th>
                  <th>Germany</th>
                  <th>Japan</th>
                  <th>Russia</th>
                </tr>
              </thead>
              <tbody>
                {sizeTable.map(row => (
                  <tr
                    key={row.size}
                    className={selectedSize === row.size ? 'highlighted' : ''}
                  >
                    <td className="size-label">
                      <strong>{row.size}</strong>
                    </td>
                    <td>{row.us.join(', ')}</td>
                    <td>{row.uk.join(', ')}</td>
                    <td>{row.italy.join(', ')}</td>
                    <td>{row.france.join(', ')}</td>
                    <td>{row.germany.join(', ')}</td>
                    <td>{row.japan.join(', ')}</td>
                    <td>{row.russia.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="size-guide-notes">
            <h3>Sizing Notes:</h3>
            <ul>
              <li>All sizes are approximate and may vary by brand and style</li>
              <li>For maternity wear, refer to your pre-pregnancy size</li>
              <li>If between sizes, we recommend sizing up for comfort</li>
              <li>Contact us if you need help choosing the right size</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SizeGuide;
