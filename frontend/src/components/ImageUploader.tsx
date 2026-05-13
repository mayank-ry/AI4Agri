/* eslint-disable @next/next/no-img-element */
import React, { ChangeEvent, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ImageUploaderProps {
  file: File | null;
  setFile: (file: File | null) => void;
  preview: string | null;
  setPreview: (url: string | null) => void;
  disabled?: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  setFile,
  preview,
  setPreview,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files?.length) return;
    const selectedFile = files[0];
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
  };

  const onSelect = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files);
  };

  const clearSelection = () => {
    setFile(null);
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <Card
      className={cn(
        "border-dashed border-2 border-green-300 bg-green-50 transition hover:bg-green-100",
        disabled && "cursor-not-allowed opacity-50"
      )}
    >
      <CardContent className="flex flex-col items-center justify-center p-6">
        {preview ? (
          <div className="flex w-full flex-col items-center">
            <img
              src={preview}
              alt="Selected crop leaf preview"
              className="mb-4 h-48 w-full rounded-xl object-cover shadow-md"
            />
            <Button variant="destructive" onClick={clearSelection} className="mt-2">
              Change photo
            </Button>
          </div>
        ) : (
          <label className="flex h-48 w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-green-300 bg-green-50 text-center transition hover:bg-green-100">
            <span className="mb-2 text-3xl text-green-600">Upload</span>
            <span className="px-3 font-medium text-green-800">
              Camera se photo lein ya gallery se chunein
            </span>
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              className="hidden"
              onChange={onSelect}
              disabled={disabled}
            />
          </label>
        )}

        <div className="mt-4 flex gap-4">
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
          >
            Gallery
          </Button>
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
          >
            Camera
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
