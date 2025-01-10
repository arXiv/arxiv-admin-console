import React from 'react';
import { TopToolbar, ToolbarProps, SaveButton } from 'react-admin';

const SaveOnlyActions: React.FC<ToolbarProps> = (props) => {
    return (
        <TopToolbar {...props}>
            <SaveButton />
        </TopToolbar>
    );
};

export default SaveOnlyActions;
