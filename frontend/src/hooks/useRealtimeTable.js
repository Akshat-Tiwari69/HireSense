import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../config/supabaseClient'

/**
 * Generic hook for realtime table subscriptions
 * @param {string} tableName - The database table to subscribe to
 * @param {Array} initialData - Initial data to populate the state
 * @param {Object} options - Additional options
 * @returns {Object} { data, setData, isConnected, refresh }
 */
export const useRealtimeTable = (tableName, initialData = [], options = {}) => {
    const [data, setData] = useState(initialData)
    const [isConnected, setIsConnected] = useState(false)
    const {
        onInsert,
        onUpdate,
        onDelete,
        filter = null
    } = options

    useEffect(() => {
        // Skip if supabase client is not configured
        if (!supabase) {
            console.warn(`⚠️ Realtime not available for table: ${tableName}. Configure VITE_SUPABASE_ANON_KEY in .env.local`)
            return
        }

        // Create a unique channel name
        const channelName = `${tableName}_realtime_${Date.now()}`

        // Set up the realtime subscription
        const channel = supabase
            .channel(channelName)
            .on(
                'postgres_changes',
                {
                    event: '*', // Listen to all events (INSERT, UPDATE, DELETE)
                    schema: 'public',
                    table: tableName,
                    filter: filter // Optional filter like "id=eq.1"
                },
                (payload) => {
                    console.log(`[${tableName}] Realtime event:`, payload.eventType, payload)
                    handleRealtimeEvent(payload)
                }
            )
            .subscribe((status) => {
                console.log(`[${tableName}] Subscription status:`, status)
                setIsConnected(status === 'SUBSCRIBED')
            })

        const handleRealtimeEvent = (payload) => {
            const { eventType, new: newRecord, old: oldRecord } = payload

            if (eventType === 'INSERT') {
                setData(prev => {
                    // Check if record already exists to avoid duplicates
                    const exists = prev.some(item => item.id === newRecord.id)
                    if (exists) return prev

                    const updated = [...prev, newRecord]
                    onInsert?.(newRecord, updated)
                    return updated
                })
            }
            else if (eventType === 'UPDATE') {
                setData(prev => {
                    const updated = prev.map(item =>
                        item.id === newRecord.id ? newRecord : item
                    )
                    onUpdate?.(newRecord, oldRecord, updated)
                    return updated
                })
            }
            else if (eventType === 'DELETE') {
                setData(prev => {
                    const updated = prev.filter(item => item.id !== oldRecord.id)
                    onDelete?.(oldRecord, updated)
                    return updated
                })
            }
        }

        // Cleanup subscription on unmount
        return () => {
            console.log(`[${tableName}] Unsubscribing from realtime`)
            supabase.removeChannel(channel)
        }
    }, [tableName, filter])

    // Manual refresh function
    const refresh = useCallback((newData) => {
        setData(newData)
    }, [])

    return {
        data,
        setData,
        isConnected,
        refresh
    }
}
