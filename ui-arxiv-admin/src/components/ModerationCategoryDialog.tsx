import React, {useContext, useEffect, useState} from "react";

// Sample category data (replace with your fetch categories API call)

import { paths as adminApi } from '../types/admin-api';
import {RuntimeContext} from "../RuntimeContext";
import {useDataProvider, useRefresh} from "react-admin";
import CategoryChooserDialog from "./CategoryChooserDialog";

type ModeratorT = adminApi['/v1/moderators/']['get']['responses']['200']['content']['application/json'][0];

const ModerationCategoryDialog: React.FC<
    {
        open: boolean;
        setOpen: (open: boolean) => void;
        userId: number;
    }
> = ({ open, setOpen, userId }) => {
    const [moderatingCategories0, setModeratingCategories0] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const [moderatingCategories, setModeratingCategories] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const dataProvider = useDataProvider();
    const refresh = useRefresh();

    useEffect(() => {
        if (open && userId) {
            const fetchModerationDomains = async () => {
                try {
                    const { data } = await dataProvider.getList<ModeratorT>('moderators', {
                        filter: { user_id: userId },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'ASC' }
                    });

                    const cats = new Map<string, boolean>();
                    for (const domain of data) {
                        cats.set(domain.archive + "." + domain.subject_class, true);
                    }
                    setModeratingCategories0(new Map(cats));
                    setModeratingCategories(cats);
                } catch (error) {
                    console.error("Error fetching moderation domains:", error);
                }
            };

            fetchModerationDomains();
        }
    }, [open, userId, dataProvider]);


    const handleUpdate = (cat_id: string, _cats: Map<string, boolean>, on_or_off: boolean) => {
        setModeratingCategories(prevMap => {
            const newMap = new Map(prevMap);
            newMap.set(cat_id, on_or_off);
            return newMap;
        });
    };


    const handleSave = async () => {
        const deleteOperations: string[] = [];
        const createOperations: ModeratorT[] = [];

        for (const [key, value] of moderatingCategories.entries()) {
            const [archive, subject_class] = key.split(".");

            if (!value) {
                const id = `${userId}+${archive}+${subject_class}`;
                deleteOperations.push(id);
            } else if (moderatingCategories0.get(key) !== value) {
                const mod: ModeratorT = {
                    id: "",
                    user_id: userId,
                    archive: archive,
                    subject_class: subject_class,
                    is_public: true,
                    no_email: false,
                    no_web_email: false,
                    no_reply_to: false,
                    daily_update: false
                };
                createOperations.push(mod);
            }
        }

        if (deleteOperations.length > 0) {
            try {
                await dataProvider.deleteMany('moderators', { ids: deleteOperations });
            } catch (error) {
                console.error("Error deleting moderators:", error);
            }
        }

        for (const mod of createOperations) {
            try {
                await dataProvider.create('moderators', { data: mod });
            } catch (error) {
                console.error("Error creating moderator:", error);
            }
        }

        refresh();
    };


    if (!moderatingCategories) return null;

    return (
        <CategoryChooserDialog
            title="Moderation Categories"
            open={open}
            setOpen={setOpen}
            currentCategories={moderatingCategories}
            onUpdateCategory={handleUpdate}
            onSaveUpdates={handleSave}
        />

    );
};

export default ModerationCategoryDialog;
