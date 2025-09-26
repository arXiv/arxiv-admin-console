import React from 'react';
import {
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Typography,
} from '@mui/material';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';

interface StandardAccordionProps {
    title: string;
    children: React.ReactNode;
    defaultExpanded?: boolean;
}

export const StandardAccordion: React.FC<StandardAccordionProps> = ({
    title,
    children,
    defaultExpanded = false,
}) => {
    return (
        <Accordion defaultExpanded={defaultExpanded} sx={{ my: 0, py: 0 }}>
            <AccordionSummary
                sx={{
                    minHeight: '48px !important',
                    '&.Mui-expanded': {
                        minHeight: '48px !important',
                    },
                    '& .MuiAccordionSummary-content': {
                        margin: '12px 0 !important',
                    },
                    '& .MuiAccordionSummary-content.Mui-expanded': {
                        margin: '12px 0 !important',
                    },
                    '& .MuiAccordionSummary-expandIconWrapper': {
                        order: -1,
                        marginRight: 1,
                        marginLeft: 0,
                    },
                }}
            >
                <ArrowRightIcon
                    fontSize="large"
                    sx={{
                        transform: 'rotate(0deg)',
                        transition: 'transform 0.15s',
                        '.Mui-expanded &': {
                            transform: 'rotate(90deg)',
                        }
                    }}
                />
                <Typography variant="h2">{title}</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ my: 0, py: 0 }}>
                {children}
            </AccordionDetails>
        </Accordion>
    );
};