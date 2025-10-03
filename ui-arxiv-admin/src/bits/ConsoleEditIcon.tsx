import React from 'react';
import EditIcon from '@mui/icons-material/Edit';
import { SvgIconProps } from '@mui/material/SvgIcon';

const ConsoleEditIcon: React.FC<SvgIconProps> = (props) => {
    return <EditIcon {...props} sx={{ color: '#1e8bc3', ...props.sx, fontSize: '1rem' }} />;
};

export default ConsoleEditIcon;
