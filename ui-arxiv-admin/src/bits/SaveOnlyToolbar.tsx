import React from 'react';
import { Toolbar, ToolbarProps, SaveButton } from 'react-admin';

const SaveOnlyToolbar: React.FC<ToolbarProps> = (props) => {
    return (
        <Toolbar {...props}>
            <SaveButton />
        </Toolbar>
    );
};

export default SaveOnlyToolbar;
