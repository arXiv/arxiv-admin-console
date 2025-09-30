
import React, {ReactNode, useEffect, useState} from "react";
import TableCell, {TableCellProps} from "@mui/material/TableCell";

interface FieldNameCellProps extends TableCellProps {
    children: ReactNode;
    width?: string;
}


const FieldNameCell: React.FC<FieldNameCellProps> = (
    {children, width = '180px', sx,  ...props}) => (
    <TableCell
        sx={{width: width, minWidth: width, maxWidth: width, fontWeight: 700,  ...sx}}
        align="right"
        {...props}
    >
        {children}
    </TableCell>
);

export default FieldNameCell;
