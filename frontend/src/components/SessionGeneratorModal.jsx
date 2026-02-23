import React from 'react';
import { X, Loader2, Check } from 'lucide-react';

const SessionGeneratorModal = ({
    show,
    onClose,
    phoneNumber,
    step,
    loading,
    error,
    onSendOTP,
    onVerifyOTP,
    onVerify2FA,
    otpCode,
    setOtpCode,
    twoFAPass,
    setTwoFAPass
}) => {
    if (!show) return null;

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-2xl max-w-md w-full border border-gray-700">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        🔐 Generate Session
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Progress Steps */}
                    <div className="flex items-center justify-center gap-2 mb-6">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-400'
                            }`}>
                            {step > 1 ? <Check size={16} /> : '1'}
                        </div>
                        <div className={`w-12 h-1 ${step >= 2 ? 'bg-blue-500' : 'bg-gray-700'}`} />
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-400'
                            }`}>
                            {step > 2 ? <Check size={16} /> : '2'}
                        </div>
                        <div className={`w-12 h-1 ${step >= 3 ? 'bg-blue-500' : 'bg-gray-700'}`} />
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-400'
                            }`}>
                            3
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Step 1: Send OTP */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <p className="text-gray-400 text-sm">
                                We'll send an OTP code to this phone number via Telegram
                            </p>
                            <div className="bg-gray-700/50 rounded-lg p-4">
                                <p className="text-gray-400 text-xs mb-1">Phone Number</p>
                                <p className="text-white font-mono text-lg">{phoneNumber}</p>
                            </div>
                            <button
                                onClick={onSendOTP}
                                disabled={loading}
                                className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Sending...
                                    </>
                                ) : (
                                    <>
                                        📲 Send OTP Code
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Step 2: Enter OTP */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <p className="text-gray-400 text-sm">
                                Check your Telegram app for the verification code
                            </p>
                            <input
                                type="text"
                                value={otpCode}
                                onChange={(e) => setOtpCode(e.target.value)}
                                placeholder="Enter OTP code"
                                className="w-full bg-gray-700 border-none rounded-xl p-3 text-center text-2xl tracking-widest font-mono ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                                autoFocus
                                maxLength={6}
                            />
                            <button
                                onClick={onVerifyOTP}
                                disabled={loading || !otpCode}
                                className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Verifying...
                                    </>
                                ) : (
                                    <>
                                        ✅ Verify OTP
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Step 3: Enter 2FA */}
                    {step === 3 && (
                        <div className="space-y-4">
                            <p className="text-gray-400 text-sm">
                                This account has 2-Factor Authentication enabled
                            </p>
                            <input
                                type="password"
                                value={twoFAPass}
                                onChange={(e) => setTwoFAPass(e.target.value)}
                                placeholder="Enter 2FA password"
                                className="w-full bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                                autoFocus
                            />
                            <button
                                onClick={onVerify2FA}
                                disabled={loading || !twoFAPass}
                                className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Verifying...
                                    </>
                                ) : (
                                    <>
                                        🔐 Verify 2FA
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SessionGeneratorModal;
