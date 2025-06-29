import React, { useEffect, useState } from 'react';
import { Typography } from '@mui/material';
import { TextFieldProps } from 'react-admin';

interface LastLoginFieldProps extends TextFieldProps {
    index: number;
    isLoading?: boolean;
    total?: number;
    tapirSessions?: any[];
}

const TapirSessionInfo: React.FC<LastLoginFieldProps> = ({index, isLoading, total, tapirSessions}) => {
    if (isLoading) return <Typography variant="body1">Loading...</Typography>;
    if (!tapirSessions || tapirSessions.length === 0) return null;

    const value = index >= 0 ? tapirSessions[index]?.start_time : total;
    console.log("tapir session info: " + value + " (" + index + "/" + total );

    return (<span> {value} </span>);
};

export default TapirSessionInfo;
