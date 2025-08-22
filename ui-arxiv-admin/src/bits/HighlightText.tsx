import React from 'react';
import Typography from "@mui/material/Typography";


interface HighlightProps {
    text: string;
    highlighters: string[];
    secondary?: string[]
}

const HighlightText: React.FC<HighlightProps> = ({ text, highlighters, secondary }) => {
    if (!highlighters || highlighters.length === 0) {
        return <Typography>{text}</Typography>;
    }

    const needles = highlighters.concat(secondary || []);
    const pattern = new RegExp(`(${needles.join('|')})`, 'gi');

    const parts = text.split(pattern);

    return (
        <Typography component="span">
            {parts.map((part, index) =>
                highlighters.some(k => k.toLowerCase() === part.toLowerCase()) ? (
                    <span
                        key={index}
                        style={{ backgroundColor: 'yellow', fontWeight: 'bold', color: 'red', border: '2px solid white' }}
                    >
                        {part}
                    </span>
                ) :
                    (
                        (secondary || []).some(k => k.toLowerCase() === part.toLowerCase()) ? (
                            <span
                                key={index}
                                style={{ backgroundColor: 'blueviolet', fontWeight: 'bold', color: 'white', textDecoration: 'underline' }}
                            >
                                {part}
                            </span>
                        ) :
                            <span key={index}>{part}</span>
                    )
            )}
        </Typography>
    );
};

export default HighlightText;
