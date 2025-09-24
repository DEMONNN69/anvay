import React from 'react';

interface ImagePreviewProps {
  file: File;
}

const ImagePreview: React.FC<ImagePreviewProps> = ({ file }) => {
  const [imageUrl, setImageUrl] = React.useState<string>('');

  React.useEffect(() => {
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800">Image Preview</h3>
      </div>
      <div className="p-4">
        <div className="relative">
          <img
            src={imageUrl}
            alt="Product preview"
            className="w-full h-64 object-contain bg-gray-50 rounded-lg"
          />
        </div>
      </div>
    </div>
  );
};

export default ImagePreview;