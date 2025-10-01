import React from 'react';
import { Box, Typography } from '@mui/material';
import { useRecordContext } from 'react-admin';

interface DottedLineRowProps {
    label: string;
    children: React.ReactNode;
    noDots?: boolean;
    hideIfEmpty?: boolean;
}

export const DottedLineRow: React.FC<DottedLineRowProps> = ({ label, children, noDots, hideIfEmpty = true }) => {
    const record = useRecordContext();

    // For react-admin components, check if they would render empty content
    const getIsEmpty = () => {
        if (!children) return true;

        if (typeof children === 'string' && children.trim() === '') {
            return true;
        }

        // Check if it's a react-admin component
        if (React.isValidElement(children) && children.props) {
            const { source, emptyText, reference } = children.props;

            // For ReferenceField components, we can't easily determine if they're empty
            // since they fetch data separately. Skip isEmpty check for these.
            if (reference) {
                return false;
            }

            // For regular TextField components with source prop
            if (source && record) {
                const value = record[source];
                return !value || (typeof value === 'string' && value.trim() === '');
            }

            // For other React elements, check their children
            if (children.props.children === '' ||
                children.props.children === null ||
                children.props.children === undefined) {
                return true;
            }
        }

        return false;
    };

    const isEmpty = getIsEmpty();

    return (
        <Box display="flex" alignItems="center">
            <Typography variant="body2" sx={{ minWidth: 0, color: '#c4d82e', fontSize: '1em' }}>
                {label}
            </Typography>
            {
                (noDots || (hideIfEmpty && isEmpty)) ? null :
                    <Box sx={{
                        flex: 1,
                        mx: 1,
                        display: 'flex',
                        alignItems: 'baseline',
                        '&::before': {
                            content: '""',
                            flex: 1,
                            height: '1px',
                            background: 'repeating-linear-gradient(to right, #ccc 0px, #ccc 3px, transparent 3px, transparent 8px)',
                            marginTop: '8px'
                        }
                    }} />
            }

            <Box sx={{
                textAlign: 'right',
                color: '#F0F5CF',
                fontSize: '1em',
                '& *': {
                    color: '#F0F5CF !important'
                }
            }}>
                {children}
            </Box>
        </Box>
    );
};