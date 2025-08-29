import React, { useState, useEffect } from "react";
import { TextInput, TextInputProps } from "react-admin";

interface IPv4AddressInputProps extends Omit<TextInputProps, 'parse' | 'format'> {
    source: string;
}

const numberToIp = (num: number): string => {
    if (!num || num === 0) return "";
    
    // Ensure we're working with unsigned 32-bit integer
    const unsignedNum = num >>> 0;
    
    const a = (unsignedNum >>> 24) & 0xFF;
    const b = (unsignedNum >>> 16) & 0xFF;
    const c = (unsignedNum >>> 8) & 0xFF;
    const d = unsignedNum & 0xFF;
    
    return `${a}.${b}.${c}.${d}`;
};

const ipToNumber = (ip: string): number => {
    if (!ip || ip.trim() === "") return 0;
    
    const parts = ip.split('.');
    if (parts.length !== 4) return 0;
    
    const nums = parts.map(part => parseInt(part, 10));
    
    // Validate each octet
    for (const num of nums) {
        if (isNaN(num) || num < 0 || num > 255) {
            return 0;
        }
    }
    
    // Use unsigned right shift to ensure unsigned 32-bit result
    return ((nums[0] << 24) + (nums[1] << 16) + (nums[2] << 8) + nums[3]) >>> 0;
};

const isValidIPv4 = (ip: string): boolean => {
    if (!ip || ip.trim() === "") return true; // Allow empty
    
    const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
    const match = ip.match(ipv4Regex);
    
    if (!match) return false;
    
    const parts = match.slice(1).map(part => parseInt(part, 10));
    return parts.every(part => part >= 0 && part <= 255);
};

const IPv4AddressInput: React.FC<IPv4AddressInputProps> = ({
    source,
    ...props
}) => {
    const formatValue = (value: any): string => {
        // Don't format if it's already a string (during typing)
        if (typeof value === 'string') {
            return value;
        }
        // Only format numeric values to IP when loading from database
        return numberToIp(value || 0);
    };

    const parseValue = (value: string): number => {
        if (!value || value.trim() === "") return 0;
        
        // Allow partial input during typing - only parse complete IPs
        if (isValidIPv4(value)) {
            return ipToNumber(value);
        }
        
        // For incomplete input, return the string as-is to allow continued typing
        return value as any;
    };

    const validateValue = (value: any) => {
        if (!value) return undefined; // Allow empty
        
        // If it's a number, convert to IP string for validation
        let ipString: string;
        if (typeof value === 'number') {
            ipString = numberToIp(value);
        } else if (typeof value === 'string') {
            ipString = value.trim();
            if (ipString === "") return undefined;
            
            // Don't validate incomplete input (allow partial typing)
            const parts = ipString.split('.');
            if (parts.length < 4) return undefined;
        } else {
            return undefined;
        }
        
        if (!isValidIPv4(ipString)) {
            return "Please enter a valid IPv4 address (e.g., 192.168.1.1)";
        }
        
        return undefined;
    };

    return (
        <TextInput
            source={source}
            format={formatValue}
            parse={parseValue}
            validate={validateValue}
            placeholder="192.168.1.1"
            {...props}
        />
    );
};

export default IPv4AddressInput;