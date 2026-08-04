import React from 'react';
import './SettingsPage.css';

const SettingsPage: React.FC = () => {
  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <h1 className="font-display-lg text-on-surface">Cài đặt</h1>
        </div>

        <div className="settings-card">
          <h3 className="font-label-md uppercase tracking-wider text-on-surface-variant">
            Về Trợ lý Pháp lý AI
          </h3>
          <p className="font-body-md text-on-surface-variant settings-description">
            Trợ lý AI tra cứu quy định pháp luật Việt Nam, trả lời có trích dẫn nguồn từ văn bản
            pháp luật thật. Câu trả lời có thể chưa đầy đủ hoặc mắc sai sót — không thay thế tư
            vấn pháp lý chuyên nghiệp.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
