import React, { useState } from 'react';
import {
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Typography,
    Box,
} from '@mui/material';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';

interface LazyAccordionProps {
    title: string;
    children: React.ReactNode;
    summary?: string;
    defaultExpanded?: boolean;
}

export const LazyAccordion: React.FC<LazyAccordionProps> = ({
    title,
    children,
    summary,
    defaultExpanded = false,
}) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);
    const [hasBeenExpanded, setHasBeenExpanded] = useState(defaultExpanded);

    const handleChange = (event: React.SyntheticEvent, expanded: boolean) => {
        setIsExpanded(expanded);
        if (expanded && !hasBeenExpanded) {
            setHasBeenExpanded(true);
        }
    };

    return (
        <Accordion
            expanded={isExpanded}
            onChange={handleChange}
            sx={{
                my: 0,
                py: 0,
                '&.MuiAccordion-root': {
                    margin: 0,
                },
                '&.MuiAccordion-root:before': {
                    display: 'none',
                },
                '&.MuiAccordion-root.Mui-expanded': {
                    margin: 0,
                }
            }}
        >
            <AccordionSummary
                sx={{
                    minHeight: '48px !important',
                    '&.Mui-expanded': {
                        minHeight: '48px !important',
                        margin: 0,
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
                <Box display="flex" alignItems="baseline">
                    <Typography variant="h2">{title}</Typography>
                    {summary && <Typography variant="body2" ml={3}>{summary}</Typography>}
                </Box>
            </AccordionSummary>
            <AccordionDetails sx={{ my: 0, py: 0 }}>
                {hasBeenExpanded && children}
            </AccordionDetails>
        </Accordion>
    );
};