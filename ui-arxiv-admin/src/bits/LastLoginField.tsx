import React, {useEffect, useState} from 'react';
import {Card, CardContent, CardHeader, Grid, Button, Typography} from '@mui/material';

import {
    useDataProvider,
    useRecordContext,
    RecordContextProvider,
    TextFieldProps,
    ConfigurableDatagridColumn
} from 'react-admin';

interface LastLoginFieldProps extends TextFieldProps {
    record?: any
}

const LastLoginField: React.FC<LastLoginFieldProps> = (props) => {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [tapirSessions, setTapirSessions] = useState<any[]>([]);
    const {source} = props;

    useEffect(() => {
        if (record) {
            const fetchTapirSessionsForUser = async () => {
                try {
                    const response = await dataProvider.getList('tapir_sessions', {
                            filter: {
                                "user_id": record.user_id,
                                "_sort": "id",
                                "_order": "DESC"
                            }
                        }
                    );

                    setTapirSessions(response.data);
                } catch (e) {

                }
            };

            fetchTapirSessionsForUser();
        }

    }, [source, record, dataProvider]);

    if (!record || !source) return null;
    if (!tapirSessions || tapirSessions.length === 0) return null;
    const latestSession = tapirSessions[0];

    return (
        <Typography variant="body1">{latestSession?.start_time}</Typography>
    );
};

export default LastLoginField;
