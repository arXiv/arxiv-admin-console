import React from 'react';
import Typography from "@mui/material/Typography";


interface HighlightProps {
    text: string;
    highlighters: string[];
}

const HighlightText: React.FC<HighlightProps> = ({ text, highlighters }) => {
    if (!highlighters || highlighters.length === 0) {
        return <Typography>{text}</Typography>;
    }

    const pattern = new RegExp(`(${highlighters.join('|')})`, 'gi');
    const parts = text.split(pattern);

    return (
        <Typography component="span">
            {parts.map((part, index) =>
                highlighters.some(k => k.toLowerCase() === part.toLowerCase()) ? (
                    <span
                        key={index}
                        style={{ backgroundColor: 'yellow', fontWeight: 'bold', color: 'red' }}
                    >
                        {part}
                    </span>
                ) : (
                    <span key={index}>{part}</span>
                )
            )}
        </Typography>
    );
};

export default HighlightText;
