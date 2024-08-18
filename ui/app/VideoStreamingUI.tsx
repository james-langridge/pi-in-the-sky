"use client"

import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const VideoStreamingUI = () => {
    const [showControls, setShowControls] = useState(false);

    function applyPreset(presetName: string) {
        fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/apply_preset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ preset: presetName }),
        })
            .then(response => response.json())
            .catch(error => console.error('Error:', error));
    }

    function shutdown() {
        if(confirm('Are you sure you want to shut down?')) fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/shutdown`)
    }

    return (
        <div className="flex flex-col h-screen bg-gray-100">
                <div className="flex-grow flex justify-center items-center overflow-hidden bg-black relative">
                <img src={`${process.env.NEXT_PUBLIC_BASE_URL}/video_feed`} alt="Video stream" className="max-w-full max-h-full object-contain" />
                <button
                    onClick={() => setShowControls(!showControls)}
                    className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-white bg-opacity-50 rounded-full p-2"
                >
                    {showControls ? <ChevronDown /> : <ChevronUp />}
                </button>
                </div>

            <div className={`bg-white shadow-lg transition-all duration-300 ease-in-out ${showControls ? 'h-auto' : 'h-0 overflow-hidden'}`}>
                <div className="p-4 max-w-lg mx-auto">
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                        <div className="col-span-2 sm:col-span-3 lg:col-span-4 flex flex-wrap justify-between gap-2 mb-2">
                            <button onClick={() => applyPreset('default')} className="bg-green-500 text-white px-4 py-2 rounded flex-grow">Default</button>
                            <button onClick={() => applyPreset('low_light')} className="bg-green-500 text-white px-4 py-2 rounded flex-grow">Low light</button>
                            <button onClick={() => shutdown()} className="bg-red-500 text-white px-4 py-2 rounded flex-grow">Shut down</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoStreamingUI;