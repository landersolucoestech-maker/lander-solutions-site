function crmMockIds(scope){let sequence=0;return (prefix)=>`mock_${scope}_${prefix}_${String(++sequence).padStart(3,'0')}`;}
