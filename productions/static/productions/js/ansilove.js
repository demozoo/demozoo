var AnsiLove = (function () {
    "use strict";
    var Palette, Font, Parser, Popup;
    // Fetches a file located at <url>, returned as a Uint8Array. <callback> is called upon success, returning the array, <callbackFail> is called, if specified, if the operation was unsucessful with the http code.
    function httpGet(url, callback, callbackFail) {
        var http = new XMLHttpRequest();

        http.open("GET", url, true);

        http.onreadystatechange = function () {
            if (http.readyState === 4) {
                switch (http.status) {
                case 0:
                case 200:
                    callback(new Uint8Array(http.response));
                    break;
                default:
                    if (callbackFail) {
                        callbackFail(http.status);
                    }
                }
            }
        };

        http.responseType = "arraybuffer";
        http.send();
    }

    // This function returns an object that emulates basic file-handling when fed an array of bytes.
    function File(bytes) {
        // pos points to the current position in the 'file'. SAUCE_ID, COMNT_ID, and commentCount are used later when parsing the SAUCE record.
        var pos, SAUCE_ID, COMNT_ID, commentCount;

        // Raw Bytes for "SAUCE" and "COMNT", used when parsing SAUCE records.
        SAUCE_ID = new Uint8Array([0x53, 0x41, 0x55, 0x43, 0x45]);
        COMNT_ID = new Uint8Array([0x43, 0x4F, 0x4D, 0x4E, 0x54]);

        // Returns an 8-bit byte at the current byte position, <pos>. Also advances <pos> by a single byte. Throws an error if we advance beyond the length of the array.
        this.get = function () {
            if (pos >= bytes.length) {
                throw "Unexpected end of file reached.";
            }
            return bytes[pos++];
        };

        // Same as get(), but returns a 16-bit byte. Also advances <pos> by two (8-bit) bytes.
        this.get16 = function () {
            var v;
            v = this.get();
            return v + (this.get() << 8);
        };

        // Same as get(), but returns a 32-bit byte. Also advances <pos> by four (8-bit) bytes.
        this.get32 = function () {
            var v;
            v = this.get();
            v += this.get() << 8;
            v += this.get() << 16;
            return v + (this.get() << 24);
        };

        // Exactly the same as get(), but returns a character symbol, instead of the value. e.g. 65 = "A".
        this.getC = function () {
            return String.fromCharCode(this.get());
        };

        // Returns a string of <num> characters at the current file position, and strips the trailing whitespace characters. Advances <pos> by <num> by calling getC().
        this.getS = function (num) {
            var string;
            string = "";
            while (num-- > 0) {
                string += this.getC();
            }
            return string.replace(/\s+$/, '');
        };

        // Returns a string of <num> characters at the current file position which is terminated by a null character.
        this.getSZ = function (num) {
            var string, value;
            string = "";
            while (num-- > 0) {
                value = this.get();
                if (value === 0) {
                    break;
                }
                string += String.fromCharCode(value);
            }
            return string;
        };

        // Returns "true" if, at the current <pos>, a string of characters matches <match>. Does not increment <pos>.
        this.lookahead = function (match) {
            var i;
            for (i = 0; i < match.length; ++i) {
                if ((pos + i === bytes.length) || (bytes[pos + i] !== match[i])) {
                    break;
                }
            }
            return i === match.length;
        };

        // Returns an array of <num> bytes found at the current <pos>. Also increments <pos>.
        this.read = function (num) {
            var t;
            t = pos;
            // If num is undefined, return all the bytes until the end of file.
            num = num || this.size - pos;
            while (++pos < this.size) {
                if (--num === 0) {
                    break;
                }
            }
            return bytes.subarray(t, pos);
        };

        // Sets a new value for <pos>. Equivalent to seeking a file to a new position.
        this.seek = function (newPos) {
            pos = newPos;
        };

        // Returns the value found at <pos>, without incrementing <pos>.
        this.peek = function (num) {
            num = num || 0;
            return bytes[pos + num];
        };

        // Returns the the current position being read in the file, in amount of bytes. i.e. <pos>.
        this.getPos = function () {
            return pos;
        };

        // Returns true if the end of file has been reached. <this.size> is set later by the SAUCE parsing section, as it is not always the same value as the length of <bytes>. (In case there is a SAUCE record, and optional comments).
        this.eof = function () {
            return pos === this.size;
        };

        // Seek to the position we would expect to find a SAUCE record.
        pos = bytes.length - 128;
        // If we find "SAUCE".
        if (this.lookahead(SAUCE_ID)) {
            this.sauce = {};
            // Read "SAUCE".
            this.getS(5);
            // Read and store the various SAUCE values.
            this.sauce.version = this.getS(2); // String, maximum of 2 characters
            this.sauce.title = this.getS(35); // String, maximum of 35 characters
            this.sauce.author = this.getS(20); // String, maximum of 20 characters
            this.sauce.group = this.getS(20); // String, maximum of 20 characters
            this.sauce.date = this.getS(8); // String, maximum of 8 characters
            this.sauce.fileSize = this.get32(); // unsigned 32-bit
            this.sauce.dataType = this.get(); // unsigned 8-bit
            this.sauce.fileType = this.get(); // unsigned 8-bit
            this.sauce.tInfo1 = this.get16(); // unsigned 16-bit
            this.sauce.tInfo2 = this.get16(); // unsigned 16-bit
            this.sauce.tInfo3 = this.get16(); // unsigned 16-bit
            this.sauce.tInfo4 = this.get16(); // unsigned 16-bit
            // Initialize the comments array.
            this.sauce.comments = [];
            commentCount = this.get(); // unsigned 8-bit
            this.sauce.flags = this.get(); // unsigned 8-bit
            this.sauce.tInfoS = this.getSZ(22); // Null-terminated string, maximum of 22 characters
            if (commentCount > 0) {
                // If we have a value for the comments amount, seek to the position we'd expect to find them...
                pos = bytes.length - 128 - (commentCount * 64) - 5;
                // ... and check that we find a COMNT header.
                if (this.lookahead(COMNT_ID)) {
                    // Read COMNT ...
                    this.getS(5);
                    // ... and push everything we find after that into our <this.sauce.comments> array, in 64-byte chunks, stripping the trailing whitespace in the getS() function.
                    while (commentCount-- > 0) {
                        this.sauce.comments.push(this.getS(64));
                    }
                }
            }
        }
        // Seek back to the start of the file, ready for reading.
        pos = 0;

        if (this.sauce) {
            // If we have found a SAUCE record, and the fileSize field passes some basic sanity checks...
            if (this.sauce.fileSize > 0 && this.sauce.fileSize < bytes.length) {
                // Set <this.size> to the value set in SAUCE.
                this.size = this.sauce.fileSize;
            } else {
                // If it fails the sanity checks, just assume that SAUCE record can't be trusted, and set <this.size> to the position where the SAUCE record begins.
                this.size = bytes.length - 128;
            }
        } else {
            // If there is no SAUCE record, assume that everything in <bytes> relates to an image.
            this.size = bytes.length;
        }
    }

    // Returns a sauce record i.e. File.sauce to <callback> asynchronously, for an array of <bytes>.
    function sauceBytes(bytes) {
        return new File(bytes).sauce;
    }

    // Returns a sauce record i.e. File.sauce to <callback> asynchronously, for the file found at <url>. <callbackFail> is called if unsuccesful.
    function sauce(url, callback, callbackFail) {
        httpGet(url, function (bytes) {
            callback(sauceBytes(bytes));
        }, callbackFail);
    }

    // Font collects together the functions for reading, rendering, and drawing the glyphs used on a canvas element.
    Font = (function () {
        // FONT_PRESETS stores all the predefined font characters, BASE64_CHARS is used when decoding the predefined data (in base64 format), and fontBitsBuffer is a buffer which is leveraged whenever a font is re-used to save a few cpu cycles.
        var FONT_PRESETS, BASE64_CHARS, fontBitsBuffer;

        // This object describes all the predefined font data, <width> and <height> are in pixels, <data> is a base64-encoded byte array, containing a 1-bit image for all 256 characters in sequence. <amigaFont> is referenced when rendering to make sure the font is one pixel wider.
        FONT_PRESETS = {
            "b-strict": {
                "width": 8,
                "height": 8,
                "data": "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",
                "amigaFont": true
            },
            "b-struct": {
                "width": 8,
                "height": 8,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGBgYGBgAGABsbAAAAAAAAGxs/mz+bGwAGD5gPAZ8GAAAdpx4PGrMADxmZD9sxn8AGBgwAAAAAAAMGDAwMBgMADAYDAwMGDAAAMd+PH7/GBAAGBj/GBgAAAAAAAAAGBgwAAAA/gAAAAAAAAAAABgYAAMGDBgwYMCAAnzO1tbmfIAAfAwMDAwMAHzGxgZ8wP4A/AZ8BsbGfADAwMbGxn8GAP7AfAbGxnwAfMD8xsbGfAD+xgwYMDAwAHzGxsZ8xnwAfMbGxn4GfAAAGBgAABgYAAAYGAAAGBgwAAYYYBgGAAAAAH4AfgAAAABgGAYYYAAAfMbGBnwwADB+w9/z38B9AHwGfsbGxn4A/MbGxvzG/AB8xsbAwMZ8APjMxsbGxvwAfMbGxv7AfAA8ZmZmYP5gAHbOxsZ+BnwAxsbGxv7GxgAYGBgYGBgYAH4GBsbGxnwAxsbGzPjGxgDAwMDAxsZ8AMbu/tbGxsYA/MbGxsbGxgB8xsbGxsZ8APzGxsbG/MAAfMbGxsbMfgP8xsbM+MbGAHzGxsB8BnwAYPxgZmZmPADGxsbGxsZ8AMbGxsZsbDgAxsbG1v7uxgDGxsbGfMbGAMbGxsZ+BnwA/sbGBnzA/gA8MDAwMDA8AMBgMBgMBgMBPAwMDAwMPAAYPGbDAAAAAAAAAAAAAAD/GBgOAAAAAAB8BnbOxsZ+APzGzPjGxvwAfMbAxsbGfAAGfsbGxsZ+AHzG/sDGxnwAPGZmZmD8YAB+xsbOdgZ8AMbG/sbGxsYAGAAYGBgYGAAGAB7GxsZ8AMbGxsz8xsYAYGBgYGZmPAD81tbWxsbGAMbm9t7OxsYAfMbGxsbGfAD8xsbG/MDAAHzGxsbOdgYA/MbG+MzGxgB8xsbAfAZ8AP5gZmZmZjwABsbGxsbOdgAGxsbGbHw4AAbGxtbW1nwABsbGxnzGxgAGxsbGfgZ8AP4GfMDGxv4ADhgYcBgYDgAYGBgYGBgYGHAYGA4YGHAAdtwAAAAAAAAGPOCGDjjAAAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAf3d3d3d/AAB/d3d3d38AAH93d3d3fwAAAAAAAAAAABgAGBgYGBgA//////////8cMDB8MDB+AGM+dz5jAAAAw2Y8GD4YGAAYGBgAGBgYAAAzZsxmMwAAZmYAAAAAAAB+gZ2xnYF+AB42Zj4AfwAAADNmzGYzAAD/DgAAAAAAAAAAAP4AAAAA6U9JAAAAAAD/AAAAAAAAADxmPAAAAAAAAAAYfhgAfgB4DBgwfAAAAHgMGAx4AAAAGDBgAAAAAAAAAGZmZmZ/YD56ejoKCgoAAAAAGBgAAAAAAAAAAAAcOHgYGBgAAAAAPGZmPAB+AAAAzGYzZswAAEDGTFgyZs4CQMNGTB4yZA7gM2Y8+TNnAQwADD5gY2M+YDB8xsb+xgAMGHzGxv7GADjGfMbG/sYAdtx8xsb+xgBsAHzGxv7GABhmfMbG/sYAAH/MzP/MzwB8xsDAwMZ8GHA+ZsD4wP4ADD5mwPjA/gAwzP7A+MD+AP9/Pw8ff///MBgAGBgYGAAMGAAYGBgYABhmGBgYGBgA//788Pj+//94bGb2ZmZ8ADtuAOb23s4AYDB8xsbGfAAMGHzGxsZ8ADDMfMbGxnwAbNh8xsbGfADGAHzGxsZ8AADDZhhmwwAAfM7O1ubmfAAwGMbGxsZ8ABgwxsbGxnwAEGyCxsbGfABsAMbGxsZ8ABgwxsbGfgZ8YGB8ZnxgYAB8xsbG3MbcwGAwPAZ+xn4ADBg8Bn7GfgAYZjwGfsZ+AHbcPAZ+xn4AbAA8Bn7GfgAYZjwGfsZ+AAAAPht/2G4AAHzGwMDGfBhgMHzG/sB8AAwYfMb+wHwAMMx8xv7AfAADHz9/f////zAYABgYGAwADBgAGBgYDAAYZgAYGBgMAMD4/P7+////Dz9///9/Pw9m2PzGxsbGADAYfMbGxnwAGDB8xsbGfADw/P7///788HbcfMbGxnwAbAB8xsbGfAAAGAB+ABgAAAB8ztbW5nwAYDDGxsbGfgAYMMbGxsZ+ABhmAMbGxn4A////f38/HwMYMMbGxn4GfGBgfGZmfGBg/////v78+MA=",
                "amigaFont": true
            },
            "microknight": {
                "width": 8,
                "height": 16,
                "data": "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",
                "amigaFont": true
            },
            "microknight+": {
                "width": 8,
                "height": 16,
                "data": "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",
                "amigaFont": true
            },
            "mosoul": {
                "width": 8,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGBgYGBgYGBgYGAAAGBgAAGxsbGwAAAAAAAAAAAAAAABsbGxs/v5sbP7+bGxsbAAAGBg+PmBgPDwGBnx8GBgAAAAAZmasrNjYNjZqaszMAAA4OGxsaGh2dtzczs57ewAAGBgYGDAwAAAAAAAAAAAAAAwMGBgwMDAwMDAYGAwMAAAwMBgYDAwMDAwMGBgwMAAAAABmZjw8//88PGZmAAAAAAAAGBgYGH5+GBgYGAAAAAAAAAAAAAAAAAAAGBgYGDAwAAAAAAAA//8AAAAAAAAAAAAAAAAAAAAAAAAYGBgYAAADAwYGDAwYGDAwYGDAwICAPDxmZm5ufn52dmZmPDwAADg4GBgYGBgYGBgYGBgYAAA8PAYGPDxgYGBgYGB+fgAAfHwGBhwcBgYGBgYGfHwAAAwMzMzMzMzM/v4MDAwMAAB8fGBgfHwGBgYGBgZ8fAAAPDxgYHx8ZmZmZmZmPDwAAH5+BgYGBgwMGBgYGBgYAAA8PGZmPDxmZmZmZmY8PAAAPDxmZmZmZmY+PgYGPDwAAAAAGBgYGAAAAAAYGBgYAAAAABgYGBgAAAAAGBgYGDAwAAAGBhgYYGAYGAYGAAAAAAAAAAD//wAA//8AAAAAAAAAAGBgGBgGBhgYYGAAAAAAPDxmZgYGHBwYGAAAGBgAAHx8xsbe3tbW3t7AwHh4AAA8PGZmZmZmZn5+ZmZmZgAAfHxmZnx8ZmZmZmZmfHwAAB4eMDBgYGBgYGAwMB4eAAB8fGZmZmZmZmZmZmZ8fAAAfn5gYGBgYGB4eGBgfn4AAH5+YGBgYGBgeHhgYGBgAAA8PGBgbm5mZmZmZmY+PgAAZmZmZmZmZmZ+fmZmZmYAADw8GBgYGBgYGBgYGDw8AAAODgYGBgYGBgYGBgY8PAAAxsbMzNjY8PDY2MzMxsYAAGBgYGBgYGBgYGBgYH5+AADGxu7u/v7W1sbGxsbGxgAAxsbm5vb23t7OzsbGxsYAADw8ZmZmZmZmZmZmZjw8AAB8fGZmZmZmZnx8YGBgYAAAeHjMzMzMzMzMzNzcfn4AAHx8ZmZmZmZmfHxmZmZmAAA8PGBgPDwGBgYGBgZ8fAAAfn4YGBgYGBgYGBgYGBgAAGZmZmZmZmZmZmZmZjw8AABmZmZmZmZmZjw8PDwYGAAAxsbGxsbG1tb+/u7uxsYAAMPDZmY8PBgYPDxmZsPDAADDw2ZmPDwYGBgYGBgYGAAA/v4MDBgYMDBgYMDA/PwAADw8MDAwMDAwMDAwMDw8AADAwGBgMDAYGAwMBgYDAwEBPDwMDAwMDAwMDAwMPDwAABAQODhsbMbGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP//GBgYGAwMAAAAAAAAAAAAAAAAAAA8PAYGPj5mZj4+AABgYGBgfHxmZmZmZmZ8fAAAAAAAADw8YGBgYGBgPDwAAAYGBgY+PmZmZmZmZj4+AAAAAAAAPDxmZn5+YGA8PAAAHBwwMDAwMDB8fDAwMDAAAAAAAAA+PmZmZmY+PgYGPDxgYGBgfHxmZmZmZmZmZgAAGBgAABgYGBgYGBgYDAwAAAwMAAAMDAwMDAwMDAwMeHhgYGBgZmZsbHh4bGxmZgAAGBgYGBgYGBgYGBgYDAwAAAAAAADs7P7+1tbGxsbGAAAAAAAAfHxmZmZmZmZmZgAAAAAAADw8ZmZmZmZmPDwAAAAAAAB8fGZmZmZ8fGBgYGAAAAAAPj5mZmZmPj4GBgYGAAAAAD4+YGBgYGBgYGAAAAAAAAA8PGBgPDwGBnx8AAAwMDAwfHwwMDAwMDAcHAAAAAAAAGZmZmZmZmZmPDwAAAAAAABmZmZmZmY8PBgYAAAAAAAAxsbGxtbW/v5sbAAAAAAAAMbGbGw4OGxsxsYAAAAAAABmZmZmZmY+PgYGPDwAAAAAfn4MDBgYMDB+fgAADg4YGBgYcHAYGBgYDg4AABgYGBgYGBgYGBgYGBgYGBhwcBgYGBgODhgYGBhwcAAAcnKcnAAAAAAAAAAAAAAAAA8PPDzw8MPDDw88PPDwAAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAfn5mZmZmZmZmZn5+AAAAAH5+ZmZmZmZmZmZ+fgAAAAB+fmZmZmZmZmZmfn4AAAAAAAAAAAAAAAAAAAAAAAAYGAAAGBgYGBgYGBgYGAAAAAAMDD4+bGw+PgwMAAAAABwcNjYwMHh4MDAwMH5+AABCQjw8ZmY8PEJCAAAAAAAAw8NmZjw8GBg8PBgYGBgAABgYGBgYGAAAGBgYGBgYAAA8PGBgPDxmZjw8BgY8PAAAZmZmZgAAAAAAAAAAAAAAADw8QkKdnaGhoaGdnUJCPDwcHCQkREQ8PAAAfn4AAAAAAAAzM2ZmzMxmZjMzAAAAAD4+BgYAAAAAAAAAAAAAAAAAAAAAAAD//wAAAAAAAAAAPDxCQrm5paW5uaWlQkI8PP//AAAAAAAAAAAAAAAAAAA8PGZmPDwAAAAAAAAAAAAAGBgYGH5+GBgYGAAAfn4AAHh4DAwYGDAwfHwAAAAAAAB4eAwMGBgMDHh4AAAAAAAAGBgwMGBgAAAAAAAAAAAAAAAAAABmZmZmZmZmZn9/YGA+Pnp6eno6OgoKCgoKCgAAAAAAABgYGBgAAAAAAAAAAAAAAAAAAAAAAAAAABgYMDAwMHBwMDAwMDAwAAAAAAAAODhEREREODgAAHx8AAAAAAAAzMxmZjMzZmbMzAAAAABAQMbGTExYWDIyZmbPzwICQEDGxkxMWFg+PmJixMQODsDAIyNmZiws2dkzM2dnAQEYGAAAGBgwMGBgZmY8PAAAMDAYGDw8ZmZ+fmZmZmYAAAwMGBg8PGZmfn5mZmZmAAAYGGZmPDxmZn5+ZmZmZgAAcXGOjjw8ZmZ+fmZmZmYAAGZmAAA8PGZmfn5mZmZmAAAYGCQkPDxmZn5+ZmZmZgAAHx88PDw8b298fMzMz88AAB4eMDBgYGBgMDAeHgwMGBgwMBgYfn5gYHh4YGB+fgAADAwYGH5+YGB4eGBgfn4AABgYZmZ+fmBgeHhgYH5+AABmZgAAfn5gYHh4YGB+fgAAMDAYGDw8GBgYGBgYPDwAAAwMGBg8PBgYGBgYGDw8AAAYGGZmPDwYGBgYGBg8PAAAZmYAADw8GBgYGBgYPDwAAHh4bGxmZvb2ZmZsbHh4AABxcc7O5ub29t7ezs7GxgAAMDAYGDw8ZmZmZmZmPDwAAAwMGBg8PGZmZmZmZjw8AAAYGGZmPDxmZmZmZmY8PAAAcXGOjjw8ZmZmZmZmPDwAAMPDPDxmZmZmZmZmZjw8AAAAAMbGbGw4OGxsxsYAAAAAPz9mZm5ufn52dmZm/PwAADAwGBhmZmZmZmZmZjw8AAAMDBgYZmZmZmZmZmY8PAAAGBgkJGZmZmZmZmZmPDwAAGZmAABmZmZmZmZmZjw8AAAGBggIw8NmZjw8GBgYGAAAwMDAwPz8xsb8/MDAwMAAADw8ZmZmZmxsZmZmZmxsYGAwMBgYPDwGBj4+ZmY+PgAADAwYGDw8BgY+PmZmPj4AABgYZmY8PAYGPj5mZj4+AABxcY6OPDwGBj4+ZmY+PgAAZmYAADw8BgY+PmZmPj4AABgYJCQ8PAYGPj5mZj4+AAAAAAAAfn4bG39/2Nh3dwAAAAAAADw8YGBgYGBgPDwYGDAwGBg8PGZmfn5gYDw8AAAMDBgYPDxmZn5+YGA8PAAAGBhmZjw8ZmZ+fmBgPDwAAGZmAAA8PGZmfn5gYDw8AAAwMBgYAAAYGBgYGBgMDAAADAwYGAAAGBgYGBgYDAwAABgYZmYAABgYGBgYGAwMAAAAAGZmAAAYGBgYGBgMDAAAYGD8/BgYPDxmZmZmPDwAAHFxjo4AAHx8ZmZmZmZmAAAwMBgYAAA8PGZmZmY8PAAADAwYGAAAPDxmZmZmPDwAABgYZmYAADw8ZmZmZjw8AABxcY6OAAA8PGZmZmY8PAAAAABmZgAAPDxmZmZmPDwAAAAAGBgAAP//AAAYGAAAAAAAAAICfHzOztbW5uZ8fICAMDAYGAAAZmZmZmZmPj4AAAwMGBgAAGZmZmZmZj4+AAAYGGZmAABmZmZmZmY+PgAAAABmZgAAZmZmZmZmPj4AAAwMGBgAAGZmZmY8PBgYMDBgYGBgfHxmZmZmfHxgYGBgAABmZgAAZmZmZjw8GBgwMA==",
                "amigaFont": true
            },
            "pot-noodle": {
                "width": 8,
                "height": 16,
                "data": "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GBgwMHx8BgZ2dsbGfn4AABgYZmZ8fAYGdnbGxn5+AAB2dtzcfHwGBnZ2xsZ+fgAAxsYAAHx8BgZ2dsbGfn4AAHx8xsZ8fAYGdnbGxn5+AAAAAAAAfn4bG35+yMh/fwAAAAAAAHx8xsbAwMbGfHwwMDAwGBh8fMbG3NzAwH5+AAAYGDAwfHzGxtzcwMB+fgAAGBhmZnx8xsbc3MDAfn4AAMbGAAB8fMbG3NzAwH5+AAAwMBgYAAAYGBgYGBgMDAAADAwYGAAAGBgYGBgYDAwAABgYZmYAABgYGBgYGAwMAAAAAGZmAAAYGBgYGBgMDAAAMDB+fhgYfHzGxsbGfHwAAHZ23NwAAPz8xsbGxsbGAgIwMBgYAAB8fMbGxsZ8fAAAGBgwMAAAfHzGxsbGfHwAABgYZmYAAHx8xsbGxnx8AAB2dtzcAAB8fMbGxsZ8fAAAAABsbAAAfHzGxsbGfHwAAAAAGBgAAH5+AAAYGAAAAAAAAAMDPj5ubn5+dnZ8fMDAdnbc3ICAxsbGxsbGfn4AAAwMGBiAgMbGxsbGxn5+AAAYGGZmgIDGxsbGxsZ+fgAAAADGxoCAxsbGxsbGfn4AAAwMGBiAgMbGxsZsbDg48PDw8GBgfHxmZmZmfHxgYPDwAADGxoCAxsbGxmxsODjw8A==",
                "amigaFont": true
            },
            "topaz": {
                "width": 8,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAIODOTkhISkpISE/P4eH///Dw5mZmZmBgZmZmZmZmf//g4OZmZmZg4OZmZmZg4P//+Hhz8+fn5+fn5/Pz+Hh//+Hh5OTmZmZmZmZk5OHh///gYGfn5+fh4efn5+fgYH//4GBn5+fn4eHn5+fn5+f///Dw5mZn5+RkZmZmZnBwf//mZmZmZmZgYGZmZmZmZn//8PD5+fn5+fn5+fn58PD///5+fn5+fn5+fn5mZnDw///nJyZmZOTh4eTk5mZnJz//5+fn5+fn5+fn5+fn4GB//+cnIiIgICUlJycnJycnP//nJyMjISEkJCYmJycnJz//8PDmZmZmZmZmZmZmcPD//+Dg5mZmZmDg5+fn5+fn///w8OZmZmZmZmZmZGRwMD//4ODmZmZmYODk5OZmZmZ///Dw5mZj4/Dw/HxmZnDw///gYHn5+fn5+fn5+fn5+f//5mZmZmZmZmZmZmZmcPD//+ZmZmZmZmZmZmBw8Pn5///nJycnJyclJSAgIiInJz//zw8mZnDw+fnw8OZmTw8//88PJmZw8Pn5+fn5+fn5///gID5+fPz5+fPz5+fgID//8PDz8/Pz8/Pz8/Pz8PD//8/P5+fz8/n5/Pz+fn8/P//w8Pz8/Pz8/Pz8/Pzw8P/////////////////////gIAAAAAAAAAAAAAAAAAAAAAAGBgYGBgYGBgYGAAAGBgAAGxsbGwAAAAAAAAAAAAAAABsbGxs/v5sbP7+bGxsbAAAGBg+PmBgPDwGBnx8GBgAAAAAZmasrNjYNjZqaszMAAA4OGxsaGh2dtzczs57ewAAGBgYGDAwAAAAAAAAAAAAAAwMGBgwMDAwMDAYGAwMAAAwMBgYDAwMDAwMGBgwMAAAAABmZjw8//88PGZmAAAAAAAAGBgYGH5+GBgYGAAAAAAAAAAAAAAAAAAAGBgYGDAwAAAAAAAAfn4AAAAAAAAAAAAAAAAAAAAAAAAYGBgYAAADAwYGDAwYGDAwYGDAwAAAPDxmZm5ufn52dmZmPDwAABgYODh4eBgYGBgYGBgYAAA8PGZmBgYMDBgYMDB+fgAAPDxmZgYGHBwGBmZmPDwAABwcPDxsbMzM/v4MDAwMAAB+fmBgfHwGBgYGZmY8PAAAHBwwMGBgfHxmZmZmPDwAAH5+BgYGBgwMGBgYGBgYAAA8PGZmZmY8PGZmZmY8PAAAPDxmZmZmPj4GBgwMODgAAAAAGBgYGAAAAAAYGBgYAAAAABgYGBgAAAAAGBgYGDAwAAAGBhgYYGAYGAYGAAAAAAAAAAB+fgAAfn4AAAAAAAAAAGBgGBgGBhgYYGAAAAAAPDxmZgYGDAwYGAAAGBgAAHx8xsbe3tbW3t7AwHh4AAA8PGZmZmZ+fmZmZmZmZgAAfHxmZmZmfHxmZmZmfHwAAB4eMDBgYGBgYGAwMB4eAAB4eGxsZmZmZmZmbGx4eAAAfn5gYGBgeHhgYGBgfn4AAH5+YGBgYHh4YGBgYGBgAAA8PGZmYGBubmZmZmY+PgAAZmZmZmZmfn5mZmZmZmYAADw8GBgYGBgYGBgYGDw8AAAGBgYGBgYGBgYGZmY8PAAAxsbMzNjY8PDY2MzMxsYAAGBgYGBgYGBgYGBgYH5+AADGxu7u/v7W1sbGxsbGxgAAxsbm5vb23t7OzsbGxsYAADw8ZmZmZmZmZmZmZjw8AAB8fGZmZmZ8fGBgYGBgYAAAeHjMzMzMzMzMzNzcfn4AAHx8ZmZmZnx8bGxmZmZmAAA8PGZmcHA8PA4OZmY8PAAAfn4YGBgYGBgYGBgYGBgAAGZmZmZmZmZmZmZmZjw8AABmZmZmZmZmZjw8PDwYGAAAxsbGxsbG1tb+/u7uxsYAAMPDZmY8PBgYPDxmZsPDAADDw2ZmPDwYGBgYGBgYGAAA/v4MDBgYMDBgYMDA/v4AADw8MDAwMDAwMDAwMDw8AADAwGBgMDAYGAwMBgYDAwAAPDwMDAwMDAwMDAwMPDwAABAQODhsbMbGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+GBgYGAwMAAAAAAAAAAAAAAAAAAA8PAYGPj5mZj4+AABgYGBgfHxmZmZmZmZ8fAAAAAAAADw8YGBgYGBgPDwAAAYGBgY+PmZmZmZmZj4+AAAAAAAAPDxmZn5+YGA8PAAAHBwwMHx8MDAwMDAwMDAAAAAAAAA+PmZmZmY+PgYGPDxgYGBgfHxmZmZmZmZmZgAAGBgAABgYGBgYGBgYDAwAAAwMAAAMDAwMDAwMDAwMeHhgYGBgZmZsbHh4bGxmZgAAGBgYGBgYGBgYGBgYDAwAAAAAAADs7P7+1tbGxsbGAAAAAAAAfHxmZmZmZmZmZgAAAAAAADw8ZmZmZmZmPDwAAAAAAAB8fGZm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",
                "amigaFont": true
            },
            "topaz+": {
                "width": 8,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAIODOTkhISkpISE/P4eH///Dw5mZmZmBgZmZmZmZmf//g4OZmZmZg4OZmZmZg4P//+Hhz8+fn5+fn5/Pz+Hh//+Hh5OTmZmZmZmZk5OHh///gYGfn5+fh4efn5+fgYH//4GBn5+fn4eHn5+fn5+f///Dw5mZn5+RkZmZmZnBwf//mZmZmZmZgYGZmZmZmZn//8PD5+fn5+fn5+fn58PD///5+fn5+fn5+fn5mZnDw///nJyZmZOTh4eTk5mZnJz//5+fn5+fn5+fn5+fn4GB//+cnIiIgICUlJycnJycnP//nJyMjISEkJCYmJycnJz//8PDmZmZmZmZmZmZmcPD//+Dg5mZmZmDg5+fn5+fn///w8OZmZmZmZmZmZGRwMD//4ODmZmZmYODk5OZmZmZ///Dw5mZj4/Dw/HxmZnDw///gYHn5+fn5+fn5+fn5+f//5mZmZmZmZmZmZmZmcPD//+ZmZmZmZmZmZmBw8Pn5///nJycnJyclJSAgIiInJz//zw8mZnDw+fnw8OZmTw8//88PJmZw8Pn5+fn5+fn5///gID5+fPz5+fPz5+fgID//8PAz8/Pz8/Pz8/Pz8DD//8/P5+fz8/n5/Pz+fn8/P7+wwPz8/Pz8/Pz8/PzA8P/////////////////////AAAAAAAAAAAAAAAAAAAAAAAAGBgYGBgYGBgYGAAAGBgAAGxsbGwAAAAAAAAAAAAAAABsbGxs/v5sbP7+bGxsbAAAGBg+PmBgPDwGBnx8GBgAAAMDZmasrNjYNjZqaszMAAA4OGxsaGh2dtzczs57ewAAGBgYGDAwAAAAAAAAAAAAAAMHDgwYGBgYGBgMDgcDAADA4HAwGBgYGBgYMHDgwAAAAABmZjw8//88PGZmAAAAAAAAGBgYGH5+GBgYGAAAAAAAAAAAAAAAAAAAGBgYGDAwAAAAAAAA//8AAAAAAAAAAAAAAAAAAAAAAAAYGBgYAAADAwYGDAwYGDAwYGDAwICAPDxmZm5ufn52dmZmPDwAABgYODh4eBgYGBgYGBgYAAA8PGZmBgYMDBgYMDB+fgAAPDxmZgYGHBwGBmZmPDwAABwcPDxsbMzM/v4MDAwMAAB+fmBgfHwGBgYGZmY8PAAAHBwwMGBgfHxmZmZmPDwAAH5+BgYGBgwMGBgYGBgYAAA8PGZmZmY8PGZmZmY8PAAAPDxmZmZmPj4GBgwMODgAAAAAGBgYGAAAAAAYGBgYAAAAABgYGBgAAAAAGBgYGDAwAwMGBgwMGBgMDAYGAwMAAAAAAAD//wAA//8AAAAAAADAwGBgMDAYGDAwYGDAwAAAPDxmZgYGDAwYGAAAGBgAAHx8xsbe3tbW3t7AwHh4AAA8PGZmZmZ+fmZmZmZmZgAAfHxmZmZmfHxmZmZmfHwAAB4eMDBgYGBgYGAwMB4eAAB4eGxsZmZmZmZmbGx4eAAAfn5gYGBgeHhgYGBgfn4AAH5+YGBgYHh4YGBgYGBgAAA8PGZmYGBubmZmZmY+PgAAZmZmZmZmfn5mZmZmZmYAADw8GBgYGBgYGBgYGDw8AAAGBgYGBgYGBgYGZmY8PAAAxsbMzNjY8PDY2MzMxsYAAGBgYGBgYGBgYGBgYH5+AADGxu7u/v7W1sbGxsbGxgAAxsbm5vb23t7OzsbGxsYAADw8ZmZmZmZmZmZmZjw8AAB8fGZmZmZ8fGBgYGBgYAAAeHjMzMzMzMzMzNzcfn4AAHx8ZmZmZnx8bGxmZmZmAAA8PGZmcHA8PA4OZmY8PAAAfn4YGBgYGBgYGBgYGBgAAGZmZmZmZmZmZmZmZjw8AABmZmZmZmZmZjw8PDwYGAAAxsbGxsbG1tb+/u7uxsYAAMPDZmY8PBgYPDxmZsPDAADDw2ZmPDwYGBgYGBgYGAAA/v4MDBgYMDBgYMDA/v4AADw/MDAwMDAwMDAwMD88AADAwGBgMDAYGAwMBgYDAwEBPPwMDAwMDAwMDAwM/DwAABAQODhsbMbGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP//GBgYGAwMAAAAAAAAAAAAAAAAAAA8PAYGPj5mZj4+AABgYGBgfHxmZmZmZmZ8fAAAAAAAADw8YGBgYGBgPDwAAAYGBgY+PmZmZmZmZj4+AAAAAAAAPDxmZn5+YGA8PAAAHBwwMHx8MDAwMDAwMDAAAAAAAAA+PmZmZmY+PgYGPDxgYGBgfHxmZmZmZmZmZgAAGBgAABgYGBgYGBgYDAwAAAwMAAAMDAwMDAwMDAwMeHhgYGBgZmZsbHh4bGxmZgAAGBgYGBgYGBgYGBgYDAwAAAAAAADs7P7+1tbGxsbGAAAAAAAAfHxmZmZmZmZmZgAAAAAAADw8ZmZmZmZmPDwAAAAAAAB8fGZm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",
                "amigaFont": true
            },
            "topaz500": {
                "width": 8,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGBg8PDw8GBgYGAAAGBgAAGxsbGwAAAAAAAAAAAAAAABsbGxs/v5sbP7+bGxsbAAAGBg+PmBgPDwGBnx8GBgAAAAAxsbMzBgYMDBmZsbGAAA4OGxsaGh2dtzczMx2dgAAGBgYGDAwAAAAAAAAAAAAAAwMGBgwMDAwMDAYGAwMAAAwMBgYDAwMDAwMGBgwMAAAAABmZjw8//88PGZmAAAAAAAAGBgYGH5+GBgYGAAAAAAAAAAAAAAAAAAAGBgYGDAwAAAAAAAAfn4AAAAAAAAAAAAAAAAAAAAAAAAYGBgYAAADAwYGDAwYGDAwYGDAwAAAPDxmZm5ufn52dmZmPDwAABgYODgYGBgYGBgYGH5+AAA8PGZmBgYcHDAwZmZ+fgAAPDxmZgYGHBwGBmZmPDwAABwcPDxsbMzM/v4MDB4eAAB+fmBgfHwGBgYGZmY8PAAAHBwwMGBgfHxmZmZmPDwAAH5+ZmYGBgwMGBgYGBgYAAA8PGZm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",
                "amigaFont": true
            },
            "topaz500+": {
                "width": 8,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGBg8PDw8GBgYGAAAGBgAAGxsbGwAAAAAAAAAAAAAAABsbGxs/v5sbP7+bGxsbAAAGBg+PmBgPDwGBnx8GBgAAAMDxsbMzBgYMDBmZsbGgIA4OGxsaGh2dtzczMx2dgAAGBgYGDAwAAAAAAAAAAAAAAMHDgwYGBgYGBgMDgcDAADA4HAwGBgYGBgYMHDgwAAAAABmZjw8//88PGZmAAAAAAAAGBgYGH5+GBgYGAAAAAAAAAAAAAAAAAAAGBgYGDAwAAAAAAAA//8AAAAAAAAAAAAAAAAAAAAAAAAYGBgYAAADAwYGDAwYGDAwYGDAwICAPDxmZm5ufn52dmZmPDwAABgYODgYGBgYGBgYGH5+AAA8PGZmBgYcHDAwZmZ+fgAAPDxmZgYGHBwGBmZmPDwAABwcPDxsbMzM/v4MDB4eAAB+fmBgfHwGBgYGZmY8PAAAHBwwMGBgfHxmZmZmPDwAAH5+ZmYGBgwMGBgYGBgYAAA8PGZm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",
                "amigaFont": true
            },
            "80x25": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GDgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAABwbBwADwDD4zGYzDsAAAAAAAAAAAAAD4xmAwGAxj4GDgAAAAAgODYAD4xn8wGAxj4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAAZgAABwGAwGAwGB4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAADAMAwABwGAwGAwGB4AAAAAAAGMAAgODYxmM/mMxmMAAAAAAODYOAgODYxn8xmMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAHYNhsfmw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAADAMAwAD4xmMxmMxj4AAAAAAABgeGYAGYzGYzGYzDsAAAAAAADAMAwAGYzGYzGYzDsAAAAAAAAAxgAAGMxmMxmMxj8BgYeAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAwGD4xmAwGAxj4GAwAAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAAZjMPAwfgwfgwGAwAAAAAAAHwzGY+GIzG8zGYzGMAAAAAAAAcGwwGAwfgwGAw2DgAAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAMBgABgMDAwGMxj4AAAAAAAAAAAAAAA/mAwGAwAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxmYAAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAdm4GAwGAwGAwAAAAAAAAAfgwPDMZjMZh4GD8AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxjYbDYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAAD4xmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAwGGw2GwcAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "80x25small": {
                "width": 4,
                "height": 8,
                "data": "AAAAAACQD2Bvb/CfCu5EAATu5AAE6k4ABO5OAAAGYAD/+Z//AGmWAP+Waf8CSqQABKpEAAdESAAHVVoABEpEAAjOyAACbmIABOTkAAqqCgAHpiIwaGlhYAAA7gAE5OTgBOREQATkREAALyAAAE9AAAAI8AAAb2AAAE7gAADuQAAAAAAABEQEAAqgAAAE5OQARoQsQACSSQAE5JpQBIAAAAJERCAEIiJACk5KAABOQAAAAASAAA4AAAAABAAAJEgABKqkAAxETgAMJI4ADCQsAAiORAAOhCwABIykAA4kRAAEpKQABqYiAABAQAAAQEgAAkhCAADw8AAIQkgASiQEAATuhgAErqoADKysAASopAAMqqwADoyOAA6MiAAEqOQACq6qAA5ETgAOIqQACqyqAAiIjgAK7qoACu7qAASqpAAMrIgABKqmAAysqgAGhCwADkREAAqqpAAKqkQACq7kAAqkqgAKpEQADiSOAAZERgAAhEIABiImAEoAAAAAAADwCEAAAABqpgAIyqwAAGiGAAJqpgAAToYAAkZEAABKpiQIyqoABAREAAQERIAIrKoABEREAADuqgAAyqoAAEqkAADKyAAAamIAAMqIAABoLAAE5EQAAKqmAACqpAAAqu4AAKRKAACqRAAA4s4AAkxCAARERAAIRkgAbAAAAABKrgAEqKSACgqmACQk6OBKBuYACgbmAEIG5gAEBuYAAAaGSEoE6OAKBOjghATo4AoERABKBEQAhAREAKBK6gBASuoAJA6MjgBv5wAHr6sASgSqQKAEqkCEBKpASgqkAIQKpACgqkQAoEqqQKCqqkAARoZASoyOAKpORADKyrohJU5EgCQG5gAkBEQAJASqQCQKpABsDKoAbAru6gbmDgAEpA4AQEikAAAOiAAADiIARA4EjkQOCOQEBO5AAFhQAAChoAAUFBQUWlpaWtfX19dERERERExERETMRERVXVVVAA9VVQDMRERV3VVVVVVVVQD9VVVV3wAAVV8AAETMAAAADEREREcAAERPAAAAD0REREdERAAPAABET0RERHdERFVXVVVVdwAAAHdVVVX/AAAA/1VVVXdVVQD/AABV/1VVRP8AAFVfAAAA/0REAA9VVVVXAABEdwAAAHdERAAHVVVVX1VVRP9ERERMAAAAB0RE/////wAA///MzMzMMzMzM///AAAFqqUAaamSAA6oiAAA6qoA+EJI8AB6qkAAVVZIAKREQOSqpOBKrqpAaZZmkGQmmWAA+Z8AEmlkgAaOhgAGmZkADg4OAABOQOAAQkBgACQgYAJUREREREzABA4EAAWgWgBKQAAAAAZgAAAGAAADIqYgDKoAAEJGAAAAZmYAAAAAAA==",
                "amigaFont": false
            },
            "80x50": {
                "width": 9,
                "height": 8,
                "data": "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NhsN5gP4AAAAAAAP5gN5sNhsNhs94A/4AAAAAAA/4A95sNhsNhsN5gN5sNhsAAA/4A/4AAAANhs94A95sNhsGAw/4A/4AAAANhsNhs/4AAAAAAA/4A/4wGAwAAAAAA/5sNhsNhsNhsP4AAAAGAwH4wH4AAAAAAAH4wH4wGAwAAAAAAP5sNhsNhsNhs/5sNhsGAw/4w/4wGAwGAwGAw+AAAAAAAAAAAH4wGAw////////////AAAAAA//////8Hg8Hg8Hg8HgD4fD4fD4fD4f//////AAAAAAAAAdm4yG4dgAeGYzGwzGMzAA/mMwGAwGAwAAAAA/jYbDYbAA/mMYBgYGM/gAAAAfmw2GwcAAAAAZjMZjMfGAADs3AwGAwGAAfgwPDMZh4GD8ODYxn8xjYOAAODYxmMbDY7gADgwDB8ZjMPAAAAAfm22z8AAABgYfm22z8YGAHhgYD8YBgHgAAD4xmMxmMxgAAH8AH8AH8AAAGAwfgwGAAfgAMAwDAwMAAfgADAwMAwDAAfgADg2GwwGAwGAwGAwGAwGGw2DgAAwAD8AAwAAAADs3AAdm4AAAODYbBwAAAAAAAAAAAwGAAAAAAAAAAwAAAAAADwYDAY7DYPA4bBsNhsNgAAAAeAYGBgfAAAAAAAAPB4PB4AAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "armenian": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABIZn+ZhIAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAPDMw2G222w2GZh4AAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAw3O/3+22Gw2Gw2GAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAA/22mQwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAw2Gw2Gw2GwzMPAwAAAAAAAAAw2Gw2Gw2223+ZjMAAAAAAAAAw2GZh4GAwPDMw2GAAAAAAAAAw2GwzMPAwGAwGB4AAAAAAAAA/2GhgYGBgYGCw3+AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAMBgGAAAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAODYZDA8DAYDAYHgAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHM/22222222AAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGGw2GwzMPAwAAAAAAAAAAAAAGGw2G222/zMAAAAAAAAAAAAAGGZh4GB4ZmGAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwAAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAAAAdm4AAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAzGYzGYzGY3G4zjsAAAAAAAAAAAAAG22222222zeAAAAAAAAAeGYzGYzGAwH8wGAAAAAAAAAAAAAAHwzGYzGAwH8wGAwAAAAAeGYzGYzGYfwYDAYAAAAAAAAAAAAAD4zGYzGYzD+DAYDAAAAAeGYzGYzGYzwYDAYAAAAAAAAAAAAAHwzGYzGYzGeDAYDAAAAAwGA/mAwGYzGYzDwAAAAAAAAAwGA/GAwGAzGYzD4AAAAAAAAAPDMZjMZh8BgY2H8wwAAAAAAAAAAAGYzGYzGYzD4DAYDwAAAAwGA/mAwGAwHwDAYeAAAAAAAAwGAwH4wGAwGA+AYeAAAAAAAAeGYzGYzGYwGAwH8AAAAAAAAAAAAAHwzGYzGYzGAwGA/gAAAAfGMz2s1ms1ms1mYAAAAAAAAAAAAAH4xme1ms1mYwGAwAAAAADAYf2YzGYzGYzDwAAAAAAAAADAYDD+zGYzGYzD4AAAAAAAAAwGA+GYzGYzGYwGAAAAAAAAAAwGAwHwzGYzGYzGYwGAwAAAAAwGAwGAwGAwGAwH4BgAAAAAAAAAAADAYDAYDAYDAYDAfAAAAAwGA+2222222222cAAAAAAAAAwGAwH222222222ewGAwAAAAAwD8+2YzGYzGYzDwAAAAAAAGAeAYDD+zGYzGYzD4AAAAAAAAAwGAzGYzGYzD4DAYAAAAAAAAAwGAwGYzGYzGYzD4DAYDAAAAAMAwDAwMDAwGAwH4DgAAAAAAAwGAwHwzGYzGYzGYAAAAAAAAAPDMZjMZgMBjY2DcAAAAAAAAAID8DAwMDg2GYzjsAAAAAAAAAeGYzGYzGYzAYDAeAAAAAAAAAAAAAHwzGYzGYzGYDAYDAeAAAzj2cGwzGYzGYzD4AAAAAAAAAGHgYDg2GYzGYzD4AAAAAAAAAz2YzGYzGYzGYzDwAAAAAAAAADwYDGYzGYzGYzD4AAAAAAAAAeGYDBwbAYDGYzDwAAAAAAAAAAAAAAYDAYDAYDAYbG4eAAAAA4DAYDMZjMZjMZh4AAAAAAAAA4DAYDMZjMZjMZh8AAAAAAAAA+AYfGYwGAzGYzDwAAAAAAAAAAAAADwzGYzAYGBgYGAfgAAAAeGYzGYzGYzGYzGYAAAAAAAAAAAAAHwzGYzGYzGYAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAeGYzGYDAYDGwcBgGAAAAAAAAAAAAAwMAwDAwMDAwGAfgAAAAfm2222222Gw2AwGAAAAAAAAAAAAAG22222222z+AwGAwAAAAYHg2GYZhsFg42H8wwAAAAAAAAAAADg2GYzDYOBgYGAfgAAAAeGYzGYzGezGYzGYAAAAAAAAAAAAAHwzGYzGYzGeAAAAAAAAAzGYzGYzGYzGYzDwAAAAAAAAAAAAAGYzGYzGYzD4AAAAAAAAADAYzGYzGYzD4DAeAAAAAAAAADAYDGYzGYzGYzD4DAYDwAAAAeGYzDAMAwDGYzDwAAAAAAAAAAAAAG82222222z2AAAAAAAAAeGYzGYzGYzGAwGAAAAAAAAAAAAAAHwzGYzGYzGYwGAwAAAAAeGYzDwzAYDAYzDwAAAAAAAAAAAAAGYzGYzGYzD4DAYeAAAAAwGA+GYzGYzGMwGAAAAAAAAAAAAAADAYDAYDAYD4AAAAAAAAAGAwfm22222z8GAwAAAAAAAAAGAwGG82222222z2GAwGAAAAAPDMZjMfDAYH8YDAAAAAAAAAAAAAAD4ZjMZjMZj4YH8YAAAAAeGYzGYzGYzGYzDwAAAAAAAAAAAAADwzGYzGYzDwAAAAAAAAAeGw2D8Gw22222z8AAAAAAAAAeGw2D8Gw22222z8GAwGAAAAAOCIlAQAAAAAAAAAAAAAAAAAYGBgYAAAAAAAAAAAAAAAAAAAAAAAfD4fD4fD4fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "baltic": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAADAwAB4ZmEwGAwGEZh4AAAAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAAfgAADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAAAAHBgGDszGYzGIzD4DGYeAAABwbBwADwDD4zGYzDsAAAAAAAAYGBgAD4xmAwGAxj4AAAAAAAAAOA0Hg4GBweCwGB4AAAAAAAAAfgAAD4xn8wGAxj4AAAAAAAAA/DMZjMfDYZjMZnMDAMPAAAAAAAAAG4djMYDAYHgGAYeAAAAAfAAABwGAwGAwGB4AAAAAAGBgAH8hgYGBgYGExn8AAAAAAAGMAAgODYxmM/mMxmMAAAAAAODYOAgODYxmM/mMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAHYNhsfmw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAAfgAAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAAAAPDMwmAwG8xmMZh0DAMPAAAAAGAwfGMwGAxj4GAwAAAAAAGBgAD4xmMYBwDGMxj4AAAAAAAAADAwAD4xjAOAYxj4AAAAAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAAAAAAD4zm89nMxj4AAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAIfGczms1ms1nM5j4QAAAAAAAAAAAAGMbBwODYxgAAAAAAAAAAAAAxj4xmMxmMfGMAAAAAAfgAEBwbGMxn8xmMxmMAAAAAAfgAPAwGAwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAGAwAH8hgYGBgYGExn8AAAAAAAAAGAwAH8zAwMDAxn8AAAAAAAAYGBgAH8zAwMDAxn8AAAAAAABsbGwAAAAAAAAAAAAAAAAAAAAwGAwGAwAAAGAwGAwGAAAAAAAAfEEmlEolEmkEfAAAAAAAAAAAfEEslUslUqkEfAAAAAAAAAAAAAAAAAAD8AgEAAAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAA8DIbDwcHA4DEZn8AAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwAAAEBwbGMxn8xmMxmMGBgHgAZh4AB4ZmEwGAwGEZh4AAAAAAAAA/jMYjQeDQYDEZn8GBgHgAGAw/jMYjQeDQYDEZn8AAAAAANhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAAAAAPAwGAwGAwGAwGB4GBgHgAbBwAD4xmAYBwDAMxj4AAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwAAAxmMxmMxmMxmMxj4MDAPAAfgAxmMxmMxmMxmMxj4AAAAAANhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsbBwAH8xkYGBgYGExn8AAAAAAAAAAAAADwDD4zGYzDsGBgHgAAAAbBwAD4xmAwGAxj4AAAAAAAAAAAAAD4xn8wGAxj4MDAPAAAAAGAwAD4xn8wGAxj4AAAAAAAAAGAwABwGAwGAwGB4GBgHgAAAAbBwAD4xjAOAYxj4AAAAAAAAAAAAAGYzGYzGYzDsMDAPAAAAAfAAAGYzGYzGYzDsAAAAAAAAAbBwAH8zAwMDAxn8AAAAAAGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAGBgAD4xmMxmMxmMxj4AAAAAAAAAeGYzGY2GYxmMxmYAAAAAAfgAAD4xmMxmMxmMxj4AAAAAADAwAGM5ns/m8zmMxmMAAAAAAAAAdm4AD4xmMxmMxj4AAAAAAdm4AD4xmMxmMxmMxj4AAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAYGBgAG4ZjMZjMZjMAAAAAAAAA5jMZjYeDwbDMZnMGAYeAAAAA4DAYDMbDweDYZnMGAYeAAAAA8DAYDAYDAYDEZn8GAYeAAAAAOAwGAwGAwGAwGB4GAYeAAAAAAAAAG4ZjMZjMZjMDAMPAAfgA/jMYjQeDQYDEZn8AAAAAAAAAAGM5ns/m8zmMxmMGAYeAAAAYGBgAAAAAAAAAAAAAAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAABsbGwAAAAAAAAAAAAAAAAAAAHAMDENnYGBgZmcmh+BgMAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAAAAAAAAAA2DYNgAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAwOAwGAwPAAAAAAAAAAAAAAAD4Bh4BgMfAAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "cyrillic": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAfGMxmc1nMxmMxj4AAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAA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",
                "amigaFont": false
            },
            "french_canadian": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GDgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAODYxggODYxmM/mMxmMAAAAAAADAMAwADwDD4zGYzDsAAAAAAAAAAD+2222z2Gw2Gw2AAAAAAAAAAAAAD4xmAwGAxj4GDgAAAAAgODYAD4xn8wGAxj4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAAZgAABwGAwGAwGB4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAAAAAAAAAAAAAAAAAAA/wA/wAGAYBggODYxmM/mMxmMAAAAAAAD4xjAODYxmMbBwDGMfAAAAADAwAH8ZjEaDwaDEZn8AAAAAAMAwAH8ZjEaDwaDEZn8AAAAAAODYAH8ZjEaDwaDEZn8AAAAAAAAgODYAD4xmMxmMxj4AAAAAAAGMAH8ZjEaDwaDEZn8AAAAAAADMAB4GAwGAwGAwGB4AAAAAAABgeGYAGYzGYzGYzDsAAAAAAADAMAwAGYzGYzGYzDsAAAAAAAAAAAAxj4xmMxmMfGMAAAAAAODYAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAwGD4xmAwGAxj4GAwAAAAAAABwbDIYHgYDAYDA5n4AAAAAAMAwAGMxmMxmMxmMxj4AAAAAAODYAGMxmMxmMxmMxj4AAAAAAAAcGwwGAwfgwGAw2DgAAAAAAAAwGAwGAwAAAGAwGAwGAAAAAAAYGBgAAAAAAAAAAAAAAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwDDwAAAAD4Bh4BgMfAAAAAAAAAAAAAAAH+AAAAAAAAAAAAAAAAAAAAAPDMAB4GAwGAwGAwGB4AAAAAAAAAAAAAAA/mAwGAwAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAHAMHENnYGBgZmcmh+BgMAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxmYAAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAdm4GAwGAwGAwAAAAAAAAAfgwPDMZjMZh4GD8AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxjYbDYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAAD4xmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAwGGw2GwcAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "greek": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAA/jEYDAYDAYDAYHgAAAAAAAAAEBwbGMxmMxmMxn8AAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAfGMxmM/mMxmMxj4AAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAAEBwbGMxmMxmMxmMAAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAA/kEAAAfAAAAAgn8AAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/mMxmMxmMxmMxmMAAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAA/mAYBgGAwMDAwH8AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAAPAwfkymUyfgwGB4AAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAGG2222222fgwGB4AAAAAAAAAPDMw2Gw2GwzMJHOAAAAAAAAAAAAAD2zmYzGYzD2AAAAAAAAAfGMxmMxn4xmMxn4wGAwAAAAAAAAAGGZh4GB4ZiEZh4AAAAAAfDAMAweGYzGYzDwAAAAAAAAAAAAAD4xmAeGAxj4AAAAAAAAA/AYGBgYGAwGAwDwDAYeAAAAAAAAAG4ZjMZjMZjMBgMBgAAAAPjGYzGfzGYzGYx8AAAAAAAAAAAAAAwGAwGAwGgYAAAAAAAAAAAAAHMbDweDYZnMAAAAAAAAAPDMBgMBh8ZjMZjMAAAAAAAAAAAAADMZjMZjMZj+YDAYAAAAAAAAAHMZjMZjYeBgAAAAAAAAA/DAwDwMDAwGAwD4BgMPAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAH+ZjMZjMZjMAAAAAAAAAAAAAB4ZjMZjMZj4YDAYAAAAAAAAAD+zGYzGYzDwAAAAAAAAAAAAAD4xmAYB4BmMfAAAAAAAAAAAAH4MBgMBgNAwAAAAAAAAAAAAAHOZjMZjMZh4AAAAAAAAAAAAAC41ms1ms1j4EAgEAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGs1ms1ms1j4EAgEAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADMw2Gw22/zMAAAAAAAAAOAgAD2zmYzGYzD2AAAAAAAAAOAgAD4xmAeGAxj4AAAAAAAAAOAgAG4ZjMZjMZjMBgMBgAAAAZgAAAwGAwGAwGgYAAAAAAAAAOAgAAwGAwGAwGgYAAAAAAAAAOAgAD4xmMxmMxj4AAAAAAAAAOAgAHOZjMZjMZh4AAAAAAAAAZgAAHOZjMZjMZh4AAAAAAAAAOAgADMw2Gw22/zMAAAAAAQEAEBwbGMxn8xmMxmMAAAAAAQEA/jMYjQeDQYDEZn8AAAAAAQEAxmMxmM/mMxmMxmMAAAAAAQEAPAwGAwGAwGAwGB4AAAAAAQEAfGMxmMxmMxmMxj4AAAAAAQEAZjMZjMPAwGAwGB4AAAAAAQEAPDMw2Gw2GwzMJHOAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAZgAPAwGAwGAwGAwGB4AAAAAAZgAZjMZjMPAwGAwGB4AAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "greek_869": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABASA4NjGYz+YzGYzGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAAAAAAAAAAH8BgMAAAAAAAAAAAwGAwGAwGAAAAwGAwGAwGAAAAAGAwEAQAAAAAAAAAAAAAAAAAAGAwCAgAAAAAAAAAAAAAAAACAvxgMBgPhgMBgMB+AAAAAAAAAAAAAAAAH+AAAAAAAAAAAAACAsxmMxmPxmMxmMxmAAAAAAABAXgYDAYDAYDAYDA8AAAAAAZgAfgwGAwGAwGAwGD8AAAAAAACAvjGYzGYzGYzGYx8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAsxmMxmHgYDAYDAYAAAAAAZgAZjMZjMPAwGAwGAwAAAAAAAAAPCEmVKoVKmSEPAAAAAAAAACAuDYxmMxmMxjYKHcAAAAAAABwbAYGBgfAAAAAAAAAAAAAAAD4DBgDAYeAAAAAAAAAAAAAAAAACAgADszGYzGYzDsAAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAACAgAD4xmAeGAxj4AAAAAAAAACAgAG4ZjMZjMZjMBgAAAAAAACAgABgMBgMBgMA4AAAAAAAAAAGYABgMBgMBgMA4AAAAAACAgAGYABgMBgMBgMA4AAAAAAAAACAgAD4xmMxmMxj4AAAAAAAAABAQAHMZjMZjMZh4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAA/mAwGAwGAwGAwGAAAAAAAAAAEBwbDYxmMxmMxn8AAAAAAAAA/mAwGA/GAwGAwH8AAAAAAAAA/gMBgYGBgYGAwH8AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAADA4DEZjYGBgYG4hgYGB8AAAAAAfGMxmMxn8xmMxj4AAAAAAAAAfgwGAwGAwGAwGD8AAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwAAAxmY2Hg4Hg2GYxmMAAAAAAAAAEBwbDYxmMxmMxmMAAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAANhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAAAAA/mMAAAfD4AAAxn8AAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwAAA/7MZjMZjMZjMZjMAAAAAAAAA/GMxmM/GAwGAwGAAAAAAANhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsAAA/mAYBgGAwMDAwH8AAAAAAAAAfgwGAwGAwGAwGAwAAAAAAAAAZjMZjMPAwGAwGAwAAAAAAAAAED41ms1msfAgEBwAAAAAAAAAxmMbDYOBwbDYxmMAAAAAAAAAEGs1ms1msfAgEBwAAAAAAAAAODYxmMxmMxjYKHcAAAAAAAAAAAAADszGYzGYzDsAAAAAAAAAeGYzGY2H4xmMxn4wEAAAAAAAAAAAEExjYOD4xmMxmMfAAGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////AAAfjAMAwfGMxmMxj4AAAAAAAAAAAAAD4xmAeGAxj4AAAAAA//////////4AAAAAAAAAAAAAAAAfgMDAwMDAYDAYB8Bh4AAAAAAAAAAG4ZjMZjMZjMBgAAAAAAAfGMxjMNh8hmMxj4AAAAAAAAAAAAABgMBgMBgMA4AAAAAAAAAAAAAGMzGw8GwzGMAAAAAAAAAfGMBgMPjMZmMxmMAAAAAAAAAAAAAGMxmMxmM5m6wGAwAAAAAAAAAEExmMxjYbBwAAAAAAAAAfgwMBgHBgYDAYB8Bh4AAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAH+ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmM5m4wGAwAAAAAAAAAD82GYzGYzDwAAAAAAAAAAAAAD4xmAwD4BgMPAAAAAAAAAAAAH4MBgMBgNg4AAAAAAAAYGAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8AAAAAAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAAAAAHMZjMZjMZh4AAAAAAAAAAAAAA4Vms1ms1j4EAgEAAAAAAAAAGEbBwOBwbEMAAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAg1ms1ms1j4EAgEAABAQADMAAAAAAAAAAAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAADMAAAAAAAAAAAAAAAAAAAAAAAAACIxmM1ms1jYAAAAAAAAAADMAHMZjMZjMZh4AAAAAABAQADMAHMZjMZjMZh4AAAAAAAAACAgACIxmM1ms1jYAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "hebrew": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/wAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZm4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAAAAxmMZjs3GYxmMAAAAAAAAAAAA+AYDAYDAYDH8AAAAAAAAAAAAOAYDAYDA4NnMAAAAAAAAAAAA/gYDAYDAYDAYAAAAAAAAAAAA/AMBgMxmMxmMAAAAAAAAAAAAcAwGAwGAwGAwAAAAAAAAAAAA/BgMBgGAwMDAAAAAAAAAAAAA/DMxmMxmMxmMAAAAAAAAAAAAzGs1mMxmMxj4AAAAAAAAAAAAcAwGAwMAAAAAAAAAAAAAAAAA/AMBgMDAYDAYDAYDgAAAAAAA/AMBgMBgMBn4AAAAAAAAAwGA/AMBgMBgYGAwAAAAAAAAAAAA/DMxmMxmMxn8AAAAAAAAAAAA3DsZmMxmMxm8AAAAAAAAAAAAOAYDAwGAwGAwGAwHAAAAAAAAOAYDAYDAYDD4AAAAAAAAAAAA/DMxmMxmMzDwAAAAAAAAAAAA7jMZjMZjMLHwAAAAAAAAAAAA+CYzGY7AYDAYDAYDgAAAAAAA/CMxmM5gMBn8AAAAAAAAAAAA7jMZjYeDAYDAYDAcAAAAAAAA7jMZhoGAYBn8AAAAAAAAAAAA/AMBjMZDYbjAYDAYAAAAAAAA/AMBgMBgMBgMAAAAAAAAAAAA1ms1ms1nsxj4AAAAAAAAAAAA/DMZjMZjM5nMAAAAAAAAwGD4xmAwGAxj4GAwAAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAAZjMPAwfgwfgwGAwAAAAAAAHwzGY+GIzG8zGYzGMAAAAAAAAcGwwGAwfgwGAw2DgAAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAMBgABgMDAwGMxj4AAAAAAAAAAAAAAA/mAwGAwAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxmYAAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAdm4GAwGAwGAwAAAAAAAAAfgwPDMZjMZh4GD8AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxjYbDYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAAD4xmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAwGGw2GwcAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "icelandic": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcHhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwGD8PAwAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAAAH8/n8AAAAAAAAAGB4fgwGAwGD8PAwfgAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAGAwGAwH8AAAAAAAAAAAAAAAABIZn+ZhIAAAAAAAAAAAAAAgEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAAAwGD4xmEwD4BkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAAAwGAwMAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGH+GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAABgMDAYGAwMBgYDAAAAAAAAAAfGMxms1ms1mMxj4AAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAAA/gAAH8AAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgMDAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAADwMBgMBgMBmMxj4AAAAAAAAA5jMbDYeD4bDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAODYxmMxmMxmMbBwAAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmMxms1n8bDYAAAAAAAAAxmMbDYOBwbDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAYDAMBgGAwDAYBgMAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZm4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAODYZDA8DAYDAYHgAAAAAAAAAAAAADszGYzGYfAYDGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1msxmMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMfDAYDA8AAAAAAAAADszGYzGYfAYDAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAADMZjMZjMPAwAAAAAAAAAAAAAGMxmM1ms/jYAAAAAAAAAAAAAGMxjYODYxmMAAAAAAAAAAAAAGMxmMxmMfgMBgYeAAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcDgGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgcGAwGDgAAAAAAAAAdm4AAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GAYOAAAAAzGYAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzGYADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAABwbBwADwDD4zGYzDsAAAAAAAAAAAAAD4xmAwGAxj4GAYOAAAAgODYAD4xn8wGAxj4AAAAAAAAAzGYAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAA+DYZjM9jMZjMbHwAAAAAAAAAbBg2AYfmMxmMxj4AAAAAAAAA8DAfDMZjMZj4YHgAAAAAAxmMEBwbGMxn8xmMxmMAAAAAAODYOAAODYxmM/mMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAHYNjs3mw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxmMAD4xmMxmMxj4AAAAAAAAA4DAYD4ZjMZjMfDAYDA8AAABgeGYAGYzGYzGYzDsAAAAAADAwADMZjMZh4GAwGB4AAAAAAAAYGBgAGMxmMxmMfgMBgYeAAxmMODYxmMxmMxmMbBwAAAAAAxmMAGMxmMxmMxmMxj4AAAAAAAAAAAABj4zm81nM5j4wAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAMPDYzmc1ms5nMbDwwAAAAAAHwzGY+GIzG8zGYzGMAAAAAAAAcGwwGAwfgwGAwGAw2DgAAAAAYGBgADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAYGBgAD4xmMxmMxj4AAAAAAAAYGBgAGYzGYzGYzDsAAAAAADAwABwbGMxn8xmMxmMAAAAAADAwAB4GAwGAwGAwGB4AAAAAADAwABwbGMxmMxmMbBwAAAAAADAwAGMxmMxmMxmMxj4AAAAAAAAAMBgABgMDAwGMxj4AAAAAAAAAAAAAAA/mAwGAAAAAAAAAAAAAAAAAAA/gMBgMAAAAAAAAAAGAwGExmYGBgYG4pgYGB8AAAAGAwGExmYGBgZmcnh8BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABmZmYZhmAAAAAAAAAAAAAAAAGYZhmZmYAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxm4AAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAADs3AwGAwGAwAAAAAAAAAPAwPDMZjMZh4GB4AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxmMxjYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAfGMxmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAw2Gw2DgAAAAAAAAAAAAGAwAD8AAwGAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAAGwbDYbDYbAAAAAAAAAAAAAAADg2BgYGQ+AAAAAAAAAAAAAAAAAAAAfD4fD4fD4fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "latin1": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GDgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAABwbBwADwDD4zGYzDsAAAAAAAAAAAAAD4xmAwGAxj4GDgAAAAAgODYAD4xn8wGAxj4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAAZgAABwGAwGAwGB4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAADAMAwABwGAwGAwGB4AAAAAAAGMAAgODYxmM/mMxmMAAAAAAODYOAgODYxmM/mMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAHYNhsfmw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAADAMAwAD4xmMxmMxj4AAAAAAABgeGYAGYzGYzGYzDsAAAAAAADAMAwAGYzGYzGYzDsAAAAAAAAAxgAAGMxmMxmMxj8BgYeAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAAAAAAD4zm89nMxj4AAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAIfGczms1ms1nM5j4QAAAAAAAAAAAAGMbBwODYxgAAAAAAAAAcGwwGAwfgwGAw2DgAAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAMBgABgMDAwGMxj4AAAAAAAAAfEEslUslUqkEfAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwYGAEBwbGMxn8xmMxmMAAAAAAfGMEBwbGMxn8xmMxmMAAAAAADAMEBwbGMxn8xmMxmMAAAAAAAAAfEEmlEolEmkEfAAAAAAAANhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAAAAAGAwfGMwGAxj4GAwAAAAAAAAAADMZh4GD8GD8GAwAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwAAAdm4ADwDD4zGYzDsAAAAAAdm4ABwbGMxn8xmMxmMAAAAAANhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsAAAAAAxj4xmMxmMfGMAAAAAAAAANAwLAMPjMZjMZh4AAAAAAAAA+DYZjM9jMZjMbHwAAAAAAODYAH8ZjEaDwaDEZn8AAAAAAAGMAH8ZjEaDwaDEZn8AAAAAAMAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAABwGAwGAwGB4AAAAAADAwAB4GAwGAwGAwGB4AAAAAAPDMAB4GAwGAwGAwGB4AAAAAAADMAB4GAwGAwGAwGB4AAAAAAGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////AAwGAwGAwAAAGAwGAwGAAAAAMAwAB4GAwGAwGAwGB4AAAAAA//////////4AAAAAAAAAAAAAGBgAD4xmMxmMxmMxj4AAAAAAAAAeGYzGY2GYxmMxmYAAAAAAODYAD4xmMxmMxmMxj4AAAAAAMAwAD4xmMxmMxmMxj4AAAAAAAAAdm4AD4xmMxmMxj4AAAAAAdm4AD4xmMxmMxmMxj4AAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAA4DAYD4ZjMZjMZj4YDA8AAAAA8DAfDMZjMZj4YHgAAAAAAGBgAGMxmMxmMxmMxj4AAAAAAODYAGMxmMxmMxmMxj4AAAAAAMAwAGMxmMxmMxmMxj4AAAAAAAAYGBgAGMxmMxmMxj8BgY+AADAwADMZjMZh4GAwGB4AAAAAAAH+AAAAAAAAAAAAAAAAAAAAAAAYGBgAAAAAAAAAAAAAAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAAAAAAAAAAAAAAAA/wA/wAAHAMDENnYGBgZmcmh+BgMAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAAAAAAAAAAAAwDDwAAAABwbDYOAAAAAAAAAAAAAAAAAAGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAwOAwGAwPAAAAAAAAAAAAAAAD4Bh4BgMfAAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "latin2": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPhsPhgMBgMDg8HAAAAAAAAAAfjMfjMZjMZjc7nYwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH4YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAAGMxmMRAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgYGBgMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnsAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAMBgGAAAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGYzGYzGYeBgAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwAAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAAAAdm4AAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4DAMfAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAADwzDwAGYzGYzGYzDsAAAAAAAAYGBgAD4xmAwGAxj4AAAAAAAAAAAAAD4xmAwGAxj4GAYeAAAAAOA0Hg4GBweCwGB4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAANjYAD4xmMxmMxmMxj4AAAAAAAAANjYAD4xmMxmMxj4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAGBgAH8hgYGBgYGExn8AAAAAAAGMEBwbGMxn8xmMxmMAAAAAADAwAB4ZmEwGAwGEZh4AAAAAAGBgYAA/jMYDwYDEZn8AAAAAAMDAAHgYDAYDAYDEZn8AAAAAAMDAAHAYDAYDAYDAYHgAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAAAA9jEZDAYDAYDEZn8AAAAAAAAA7DIaDAYDAYDAYHgAAAAAAGBgAD4xmMYBwDGMxj4AAAAAAAAADAwAD4xjAOAYxj4AAAAAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAZh4AD8fi0GAwGAwGB4AAAAAAAAMEhoMH4MBgMBgNg4AAAAAAAAA8DIbDwcHA4DEZn8AAAAAAAAAAAAAAAxjYODYxgAAAAAAAAAAbBwAD4xmAwGAxj4AAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAEBwbGMxn8xmMxmMGBgHgAAAAAAAADwDD4zGYzDsGBgHgAbBwAH8xkYGBgYGExn8AAAAAAAAAbBwAH8zAwMDAxn8AAAAAAAAA/jMYjQeDQYDEZn8GBgHgAAAAAAAAD4xn8wGAxj4MDAPAAAAAAAAAAA/gMBgMBgAAAAAAAAAYGBgAH8zAwMDAxn8AAAAAAZh4AB4ZmEwGAwGEZh4AAAAAAAAAAAAAD4xjAOAYxj4GAYeAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAADYNg2NjYAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGBgAAgODYxmM/mMxmMAAAAAAODYAAgODYxmM/mMxmMAAAAAAbBwAH8ZjEaDwaDEZn8AAAAAAAAAfGMxjAOAYBmMxj4GAYeAANhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAAGAwAH8hgYGBgYGExn8AAAAAAAAAGAwAH8zAwMDAxn8AAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwxj4AAgODYxmM/mMxmMAAAAAAAAAxj4ADwDD4zGYzDsAAAAAANhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsAAAAAAAGMfGMxmMfGMAAAAAAAAADAYfgYPDYzGYzDsAAAAAAAAA+DYZjM9jMZjMbHwAAAAAAbBwAHwbDMZjMZjMbHwAAAAAAbAAAH8ZjEaDwaDEZn8AAAAAAAAAHYbDZ4bGYzGYzDsAAAAAAbBwAGM5ns/m8zmMxmMAAAAAADAwAB4GAwGAwGAwGB4AAAAAAPDMAB4GAwGAwGAwGB4AAAAAAAAAZh4AD4xn8wGAxj4AAAAAAGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////AAAfj8WgwGAwGAwGB4GAYeAAODYOAAxmMxmMxmMxj4AAAAAA//////////4AAAAAAAAAAAAADAwAD4xmMxmMxmMxj4AAAAAAAAAeGYzGY2GYxmMxmYAAAAAAODYAD4xmMxmMxmMxj4AAAAAADAwAGM5ns/m8zmMxmMAAAAAAAAYGBgAG4ZjMZjMZjMAAAAAAAAAbBwAG4ZjMZjMZjMAAAAAAbBwAD4xmAYBwDAMxj4AAAAAAAAAbBwAD4xjAOAYxj4AAAAAAGBgAH4ZjMZj4bDMZnsAAAAAAGBgAGMxmMxmMxmMxj4AAAAAAAAYGBgAG4djMYDAYHgAAAAAANjYAGMxmMxmMxmMxj4AAAAAAAAYGBgAGMxmMxmMxj8BgY+AADAwADMZjMZh4GAwGB4AAAAAAAAAEBgMH4MBgMBgNg4GAYeAAAAYGBgAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8AAAAAAAAAAAAABsbGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMDAPAAADYOAAAAAAAAAAAAAAAAAAAAAGMfAAAAAAAAAAAAAAAAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAGAwAD8AAwGAAAAAAAAAAAAAAAAAAAAAAAAAAGAYeAAABwbDYOAAAAAAAAAAAAAAAAAADYbAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAANjYAGYzGYzGYzDsAAAAAAbBwAH4ZjMZj4bDMZnsAAAAAAAAAbBwAG4djMYDAYHgAAAAAAAAAAAAfD4fD4fD4fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "nordic": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GDgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAABwbBwADwDD4zGYzDsAAAAAAAAAAAAAD4xmAwGAxj4GDgAAAAAgODYAD4xn8wGAxj4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAAZgAABwGAwGAwGB4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAADAMAwABwGAwGAwGB4AAAAAAAGMAAgODYxmM/mMxmMAAAAAAODYOAgODYxmM/mMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAHYNhsfmw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAADAMAwAD4xmMxmMxj4AAAAAAABgeGYAGYzGYzGYzDsAAAAAAADAMAwAGYzGYzGYzDsAAAAAAAAAxgAAGMxmMxmMxj8BgYeAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAAAAAAD4xmc1nMxj4AAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAIfGczms1ms1nM5j4QAAAAAAHwzGY+GIzG8zGYzGMAAAAAAAAcGwwGAwfgwGAw2DgAAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAMBgABgMDAwGMxj4AAAAAAAAAAAAAAA/mAwGAwAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAxj4xmMxmMfGMAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxmYAAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAdm4GAwGAwGAwAAAAAAAAAfgwPDMZjMZh4GD8AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxjYbDYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAAD4xmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAwGGw2GwcAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "persian": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABIZn+ZhIAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAPDMw2G222w2GZh4AAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAw3O/3+22Gw2Gw2GAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAA/22mQwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAw2Gw2Gw2GwzMPAwAAAAAAAAAw2Gw2Gw2223+ZjMAAAAAAAAAw2GZh4GAwPDMw2GAAAAAAAAAw2GwzMPAwGAwGB4AAAAAAAAA/2GhgYGBgYGCw3+AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAMBgGAAAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAODYZDA8DAYDAYHgAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHM/22222222AAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGGw2GwzMPAwAAAAAAAAAAAAAGGw2G222/zMAAAAAAAAAAAAAGGZh4GB4ZmGAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwAAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAAAAAAAAAAAAAAAQEAgCAOAAAAAAAAAAAACAgDwAAAAAAAAAAAAAAAAAAAAAAAAgOAgAAAAAAAAAAAgEAgEAQCAQBAIBAIAAAAAAAAEQj4QBAIBAEAgEAgAAAAAAACSSTsQBAIBAEAgEAgAAAAAAAAMCAgEAYCAgIBAIA8AAAAAAAAAEAQFBIIiEQUCkTcAAAAAAACEPgEAgIBAIBAEAgEAAAAAAACEQiEQhEJBIFAwGAgAAAAAAAAQGAwFBIJBEQiEQiEAAAAAAAAwJCIRB4BAIBAEAgEAAAAAAAAAAAADAwGAwAAAAAAAAAAAAAAAAAAAAAAH+AAAAAAAAAAB4QiAQBAEAYDAAAAYDAAAAAAACPiACAQCAQCAQCAAAAAAAAAAAAAMCAcEACAX8AAAAAAAAAAAAAAAAAQEAgDAgBAQAAAAAAAACAQCAQCAQCAQCAAAAAAAAAAAIBAIBAIBAIBAGAAAAAAAAAAAAAAAAAAACCgT8AAAEAAAAAAAAAAAAAAAACAX8AAAEAAAAAAAAAAAAAAACCgT8AAAFAQAAAAAAAAAAAAAACAX8AAAKAgAAAAAAAAAFAAACCgT8AAAAAAAAAAAAAAAFAAAACAX8AAAAAAAAAAAAAAQFAAACCgT8AAAAAAAAAAAAAAQFAAAACAX8AAAAAAAAAAAAAAAAAwJAEHxAQCARCAIQ8AAAAAAAAAGBIAn+AAACAAAAAAAAAAAAAwJAEHxAQCURCAIQ8AAAAAAAAAGBIAn+AAAKAgAAAAAAAAAAAwJAEHxAQCAQCAIQ8AAAAAAAAAGBIAn+AAAAAAAAAAAAEAAAAwJAEHxAQCAQCAIQ8AAAAAgAAAGBIAn+AAAAAAAAAAAAAAAAAIAgCIQ8AAAAAAAAAAAACAAAAIAgCIQ8AAAAAAAAAAAAAAAAAAAAEAQCAQEBBwAAAAAAAAAAgAAAEAQCAQEBBwAAAAAAAAICgAAAEAQCAQEBBwAAAAAAAAAAAAABKFQ+EAgIGAAAAAAAAAAAAAAACJX8AAAAAAAAAAAAAAICgAABKFQ+EAgIGAAAAAAAAAQFAAAACJX8AAAAAAAAAAAAAAAAAAAgKKQ8EAgIGAAAAAAAAAAAAABhSMX8AAAAAAAAAAAAAAIAAAAgKKQ8EAgIGAAAAAAABAAAAABhSMX8AAAAAAAAAABAIBAIBAJhSMX8AAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVUAAAAQCAgEBEISBQEAAAAAAAAGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAw+AwGAwGAwGAwGAwGAwGAw+Aw+AwGAwGAwGAwNhsNhsNhsNhs9hsNhsNhsNhsAAAAAAAAAAAA/hsNhsNhsNhsAAAAAAAAA+Aw+AwGAwGAwGAwNhsNhsNhs9gM9hsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAAA/gM9hsNhsNhsNhsNhsNhsNhs9gM/gAAAAAAAAAANhsNhsNhsNhs/gAAAAAAAAAAGAwGAwGAw+Aw+AAAAAAAAAAAAAAAAAAAAAAA+AwGAwGAwGAwGAwGAwGAwGAwH4AAAAAAAAAAGAwGAwGAwGAw/4AAAAAAAAAAAAAAAAAAAAAA/4wGAwGAwGAwGAwGAwGAwGAwH4wGAwGAwGAwAAAAAAAAAAAA/4AAAAAAAAAAGAwGAwGAwGAw/4wGAwGAwGAwGAwGAwGAwH4wH4wGAwGAwGAwNhsNhsNhsNhsN5sNhsNhsNhsNhsNhsNhsN5gP4AAAAAAAAAAAAAAAAAAAP5gN5sNhsNhsNhsNhsNhsNhs94A/4AAAAAAAAAAAAAAAAAAA/4A95sNhsNhsNhsNhsNhsNhsN5gN5sNhsNhsNhsAAAAAAAAA/4A/4AAAAAAAAAANhsNhsNhs94A95sNhsNhsNhsGAwGAwGAw/4A/4AAAAAAAAAANhsNhsNhsNhs/4AAAAAAAAAAAAAAAAAAA/4A/4wGAwGAwGAwAAAAAAAAAAAA/5sNhsNhsNhsNhsNhsNhsNhsP4AAAAAAAAAAGAwGAwGAwH4wH4AAAAAAAAAAAAAAAAAAAH4wH4wGAwGAwGAwAAAAAAAAAAAAP5sNhsNhsNhsNhsNhsNhsNhs/5sNhsNhsNhsGAwGAwGAw/4w/4wGAwGAwGAwGAwGAwGAwGAw+AAAAAAAAAAAAAAAAAAAAAAAH4wGAwGAwGAw////////////////////////AAAAAAAAAAAA////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f////////////AAAAAAAAAAAAABAIBIIBAJhSMX8AAAAAAAAAAAAAAADAgEAQHhAQCAQCAIQ8AAAAAAAAcHgYExAQCAQCAIQ8AAAAAAAAAHB4GHOAAAAAAAAAAAAAAAAAYEggCH+AAAAAAAAAAAACAADAgEAQHhAQCAQCAIQ8AAABAAAAcHgYExAQCAQCAIQ8AAAAAQAAAHB4GHOAAAAAAAAAAAACAAAAYEggCH+AAAAAAAAAAAAAgAAAEBSOgT8AAAAAAAAAAAAAgAAAEBQOAX8AAAAAAAAAAAAAAUAAAAgKJSGQSCQREHAAAAACgAAAEBQOAX8AAAAAAAAAAACAQCCQiCQigT8AAAAAAAAAAQEBAQEAgDgCAX8AAAAAAAAABQUFAQEAwBgCgT8AAAAAAAAABQUFAQEAgDgCAX8AAAAAAAAAAACAQCAQCAQCISCQSCQR8AAAAACIRCEQiCQSBg+AAAAAAAAAAACAQCAQCAQCAX8AAAAAAAAAAAAAAAAAADAcHxAIBAIBAIBAAAAAAAAAAAAMCXsAAAAAAAAAAAAAAAAAIAACISCQSCQRCHgAAAAAAACAAAACAX8AAAAAAAAAAAAAAAAAAAgKBQGAQEBDwAAAAAAAAAAAIBgSCQMAAAAAAAAAAAAAAAAAAHBIKHmJAkDgAAAAAAAAAACAIHhKGXsAAAAAAAAAAAAAAAAAAAAAAAOCCQhEEgj4AAAAAAAAABgQSEIgkEgj4AAAAAAAAAAAAAACAX8AAAKAAAAAAAAAH+VX+VX+VX+5Xu/X+/3+",
                "amigaFont": false
            },
            "portuguese": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GDgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAdm4ADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAYGAEBwbGMxn8xmMxmMAAAAAAAAAAAAAD4xmAwGAxj4GDgAAAAAgODYAD4xn8wGAxj4AAAAAAODYAH8ZjEaDwaDEZn8AAAAAAADAMAwAD4xn8wGAxj4AAAAAADAwAB4GAwGAwGAwGB4AAAAAAODYAD4xmMxmMxmMxj4AAAAAAADAMAwABwGAwGAwGB4AAAAAAdm4ABwbGMxn8xmMxmMAAAAAAODYxhwbGMxn8xmMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAADAMEBwbGMxn8xmMxmMAAAAAAMAwAH8ZjEaDwaDEZn8AAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAdm4AD4xmMxmMxj4AAAAAAADAMAwAD4xmMxmMxj4AAAAAAGBgAGMxmMxmMxmMxj4AAAAAAADAMAwAGYzGYzGYzDsAAAAAAMAwAB4GAwGAwGAwGB4AAAAAAdm4AD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAwGD4xmAwGAxj4GAwAAAAAAABwbDIYHgYDAYDA5n4AAAAAAMAwAGMxmMxmMxmMxj4AAAAAAAHwzGY+GIzG8zGYzGMAAAAAAGBgAD4xmMxmMxmMxj4AAAAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAMBgABgMDAwGMxj4AAAAAAMAwAD4xmMxmMxmMxj4AAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAADs3Gw2Gw3DsAAAAAAAAAeGYzGY2GYxmMxmYAAAAAAAAA/mMxmAwGAwGAwGAAAAAAAAAAAAAAH8bDYbDYbDYAAAAAAAAA/mMYBgGAwMDAxn8AAAAAAAAAAAAAD82Gw2Gw2DgAAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAdm4GAwGAwGAwAAAAAAAAAfgwPDMZjMZh4GD8AAAAAAAAAODYxmM/mMxmMbBwAAAAAAAAAODYxmMxjYbDYbHcAAAAAAAAAHhgGAYPjMZjMZh4AAAAAAAAAAAAAD82222z8AAAAAAAAAAAAAAGBj82228z8YGAAAAAAAAAAHBgYDAfDAYDAMA4AAAAAAAAAAD4xmMxmMxmMxmMAAAAAAAAAAAA/gAAH8AAA/gAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAABgGAYBgYGBgAD8AAAAAAAAAAAYGBgYBgGAYAD8AAAAAAAAADg2GwwGAwGAwGAwGAwGAwGAwGAwGAwGAwGGw2GwcAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAADs3AAdm4AAAAAAAAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAeDAYDAYDHYbDYPA4AAAAAAADYNhsNhsNgAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "russian": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAfGMxmc1nMxmMxj4AAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAHhsZmMxn8xmMxmMAAAAAAAAA/jEYDAfDMZjMZn4AAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAA/jMYjAYDAYDAYHgAAAAAAAAAHhsZjMZjMZjMZn+w0CAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA222Wi0fj8Wm2222AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAAxmMxmc3ns5mMxmMAAAAAAbBwxmMxmc3ns5mMxmMAAAAAAAAA5jMbDYeDwbDYZnMAAAAAAAAAHxsZjMZjMZjMZmeAAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/mMxmMxmMxmMxmMAAAAAAAAA/DMZjMZj4YDAYHgAAAAAAAAAfGMxmAwGAwGExj4AAAAAAAAA/22mQwGAwGAwGB4AAAAAAAAAxmMxmMxj8BgMxj4AAAAAAAAAfm22222222z8GB4AAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAxmMxmMxmMxmMxn+AwGAAAAAAxmMxmMxj8BgMBgMAAAAAAAAA1ms1ms1ms1ms1n8AAAAAAAAA1ms1ms1ms1ms1n+AwGAAAAAA+HgsBgPhmMxmMz8AAAAAAAAAw2Gw2G82222223mAAAAAAAAA8DAYDAfDMZjMZn4AAAAAAAAAfGMBhMPhMBgMxj4AAAAAAAAAzm2222+2222222cAAAAAAAAAPzMZjMPh8ZjMZnOAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAEBj4wGA/GMxmMxj4AAAAAAAAAAAAAH4ZjMfDMZn4AAAAAAAAAAAAAH8YjEYDAYHgAAAAAAAAAAAAAA8NjMZjMZn+w2GAAAAAAAAAAD4xmM/mAxj4AAAAAAAAAAAAAGs1iofCo1msAAAAAAAAAAAAAD4xgMPAMxj4AAAAAAAAAAAAAGMxmc1nMxmMAAAAAAAAAADYOGMxmc1nMxmMAAAAAAAAAAAAAHMbDweDYZnMAAAAAAAAAAAAAA8NjMZjMZnMAAAAAAAAAAAAAGM7n8/ms1mMAAAAAAAAAAAAAGMxmM/mMxmMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAH8xmMxmMxmMAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwGAwGAwGHwGHwGAwGAwGAwGAwNhsNhsNhsNnsNhsNhsNhsNhsAAAAAAAAAAH8NhsNhsNhsNhsAAAAAAAHwGHwGAwGAwGAwGAwNhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAANhsNhsNhsNn8AAAAAAAAAAAAGAwGAwGHwGHwAAAAAAAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwGAwGAwGA/GA/GAwGAwGAwGAwNhsNhsNhsNhvNhsNhsNhsNhsNhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsGAwGAwGH/AH/AAAAAAAAAAAANhsNhsNhsNn/AAAAAAAAAAAAAAAAAAAH/AH/GAwGAwGAwGAwAAAAAAAAAAH/NhsNhsNhsNhsNhsNhsNhsNh/AAAAAAAAAAAAGAwGAwGA/GA/AAAAAAAAAAAAAAAAAAAA/GA/GAwGAwGAwGAwAAAAAAAAAAB/NhsNhsNhsNhsNhsNhsNhsNn/NhsNhsNhsNhsGAwGAwGH/GH/GAwGAwGAwGAwGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f//////////4AAAAAAAAAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAAD4xmAwGAxj4AAAAAAAAAAAAAD8WgwGAwGB4AAAAAAAAAAAAAGMxmMxmMfgMBmMfAAAAAAB4GD82222222z8GAwPAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxn+AwGAAAAAAAAAAGMxmMxj8BgMAAAAAAAAAAAAAGs1ms1ms1n8AAAAAAAAAAAAAGs1ms1ms1n8AwGAAAAAAAAAAHwsFgPhmMz8AAAAAAAAAAAAAGMxmM9m83nsAAAAAAAAAAAAAHgYDAfDMZn4AAAAAAAAAAAAAD4xgMPgMxj4AAAAAAAAAAAAAGc222+2222cAAAAAAAAAAAAAD+xmMfhsZnOAAAAAAbAA/jMYjQeDQYDEZn8AAAAAAAAAADYAD4xmM/GAxj4AAAAAAAAAfGMwGQ+GQwGAxj4AAAAAAAAAAAAAD4xmA+GAxj4AAAAAAZgAPAwGAwGAwGAwGB4AAAAAAAAAADYABwGAwGAwGB4AAAAAAbBwxmMxmMxj8BgMxj4AAAAAAAAAADYOGMxmMxmMfgMBmMfAAABwbDYOAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAcDAYDAYDAY7DYPA4AAAAAAAAAz2a73Y/243GYzGYAAAAAAAAAAGMfGMxmMxmMfGMAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "terminus": {
                "width": 9,
                "height": 16,
                "data": "AAAfiEQiEQiEQiEQj8AAAAAAAAAfEEqkEgl0kkEgj4AAAAAAAAAfH81n8/mM7n8/j4AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAEBwOAgVH8/ioEBwAAAAAAAAAEAgOD4/n8fAgEBwAAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAAAGBIJAwAAAAAAAAA/3+/3+/3+52223O/3+/3+/3+AAAHgMCgkOCIRCIRBwAAAAAAAAAOCIRCIRBwED4EAgAAAAAAAAAPhEPhAIBAIBAIGAAAAAAAAAAfiEfiEQiEQiEQiIgAAAAAAAAAAgkioOHcOCokggAAAAAAAAAAAAwHg/H+/HgwAAAAAAAAAAAAAAAweP3+PweAwAAAAAAAAAAEBwVAgEAgECoOAgAAAAAAAAAJBIJBIJBIJAAJBIAAAAAAAAAfkkkkkkjkEgkEgkAAAAAAABwRCAMCQRCIJAwBCIOAAAAAAAAAAAAAAAAAfj8fj8AAAAAAAAAEBwVAgEAgVBwED4AAAAAAAAAEBwVAgEAgEAgEAgAAAAAAAAAEAgEAgEAgECoOAgAAAAAAAAAAAAAAQBH8BAQAAAAAAAAAAAAAAAABAQH8QBAAAAAAAAAAAAAAAAQCAQCAQD8AAAAAAAAAAAAAAAABIQn+QhIAAAAAAAAAAAAAAAEAgOBwfD4/n8AAAAAAAAAAAA/n8fD4OBwEAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAgEAgEAgEAAEAgAAAAAAABIJBIAAAAAAAAAAAAAAAAAAAAAJBIJD8JBIfhIJBIAAAAAAAAgED4kkgkD4Egkkj4EAgAAAAAAZEoaAQEAgIBYUiYAAAAAAAAAGBIJAwMCURCIRB0AAAAAAAAgEAgAAAAAAAAAAAAAAAAAAAAACAgIBAIBAIBAEAQAAAAAAAAAIAgCAQCAQCAQEBAAAAAAAAAAAAAABIGD8GBIAAAAAAAAAAAAAAAAAgED4EAgAAAAAAAAAAAAAAAAAAAAAAAAEAgIAAAAAAAAAAAAAAAD8AAAAAAAAAAAAAAAAAAAAAAAAAAAEAgAAAAAAAAABAICAQEAgIBAQCAAAAAAAAAAPCEQiMSikYiEQh4AAAAAAAAACAwKAQCAQCAQCB8AAAAAAAAAPCEQgEBAQEBAQD8AAAAAAAAAPCEQgEHAEAiEQh4AAAAAAAAAAgMCgkIiEfgEAgEAAAAAAAAAfiAQCAfAEAgEQh4AAAAAAAAAHBAQCAfCEQiEQh4AAAAAAAAAfgEAgIBAQCAgEAgAAAAAAAAAPCEQiEPCEQiEQh4AAAAAAAAAPCEQiEQh8AgEBBwAAAAAAAAAAAAAAgEAAAAAEAgAAAAAAAAAAAAAAgEAAAAAEAgIAAAAAAAAAAICAgICAIAgCAIAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAACAIAgCAICAgICAAAAAAAAAAPCEQiEBAQCAACAQAAAAAAAAAfEEnlEolEpk0gD8AAAAAAAAAPCEQiEQj8QiEQiEAAAAAAAAAfCEQiEfCEQiEQj4AAAAAAAAAPCEQiAQCAQCEQh4AAAAAAAAAeCIQiEQiEQiERDwAAAAAAAAAfiAQCAeCAQCAQD8AAAAAAAAAfiAQCAeCAQCAQCAAAAAAAAAAPCEQiAQCcQiEQh4AAAAAAAAAQiEQiEfiEQiEQiEAAAAAAAAAOAgEAgEAgEAgEBwAAAAAAAAADgIBAIBAIBCIRBwAAAAAAAAAQiISCgYDAUCQRCEAAAAAAAAAQCAQCAQCAQCAQD8AAAAAAAAAgmMqkkkkEgkEgkEAAAAAAAAAQiEQjEUiURiEQiEAAAAAAAAAPCEQiEQiEQiEQh4AAAAAAAAAfCEQiEQj4QCAQCAAAAAAAAAAPCEQiEQiEQiESh4AgAAAAAAAfCEQiEQj4UCQRCEAAAAAAAAAPCEQCAPAEAiEQh4AAAAAAAAA/ggEAgEAgEAgEAgAAAAAAAAAQiEQiEQiEQiEQh4AAAAAAAAAQiEQiEQhIJBIGAwAAAAAAAAAgkEgkEgkkklUxkEAAAAAAAAAQiEJBIGAwJBIQiEAAAAAAAAAgkERCIKAgEAgEAgAAAAAAAAAfgEAgICAgICAQD8AAAAAAAAAOBAIBAIBAIBAIBwAAAAAAAAAQCAIBAEAgCAQBAIAAAAAAAAAOAQCAQCAQCAQCBwAAAAAAAAgKCIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8AAAEAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAB4Ah8QiEQh8AAAAAAAAAQCAQD4QiEQiEQj4AAAAAAAAAAAAAB4QiAQCAQh4AAAAAAAAAAgEAh8QiEQiEQh8AAAAAAAAAAAAAB4QiEfiAQB4AAAAAAAAADggED4EAgEAgEAgAAAAAAAAAAAAAB8QiEQiEQh8AgEPAAAAAQCAQD4QiEQiEQiEAAAAAAAAAEAgABgEAgEAgEBwAAAAAAAAABAIAAYBAIBAIBAIRCIOAAAAAQCAQCERCQcCQRCEAAAAAAAAAMAgEAgEAgEAgEBwAAAAAAAAAAAAAH4kkkkkkkkkAAAAAAAAAAAAAD4QiEQiEQiEAAAAAAAAAAAAAB4QiEQiEQh4AAAAAAAAAAAAAD4QiEQiEQj4QCAQAAAAAAAAAB8QiEQiEQh8AgEAgAAAAAAAAC8YCAQCAQCAAAAAAAAAAAAAAB8QCAPAEAj4AAAAAAAAAEAgED4EAgEAgEAcAAAAAAAAAAAAACEQiEQiEQh8AAAAAAAAAAAAACEQiEJBIGAwAAAAAAAAAAAAAEEgkkkkkkj4AAAAAAAAAAAAACEQhIGBIQiEAAAAAAAAAAAAACEQiEQiEQh8AgEPAAAAAAAAAD8BAQEBAQD8AAAAAAAAADAgEAgIAgEAgEAYAAAAAAAAAEAgEAgEAgEAgEAgAAAAAAAAAMAQCAQBAQCAQCBgAAAAAAADEkkYAAAAAAAAAAAAAAAAAAAAAAAAEBQREEgkEgn8AAAAAAAAAPCEQiAQCAQCEQh4EAgIAAAAAJBIACEQiEQiEQh8AAAAAAAAACAgAB4QiEfiAQB4AAAAAAAAAGBIAB4Ah8QiEQh8AAAAAAAAAJBIAB4Ah8QiEQh8AAAAAAAAAEAQAB4Ah8QiEQh8AAAAAAAAAGBIGB4Ah8QiEQh8AAAAAAAAAAAAAB4QiAQCAQh4EAgIAAAAAGBIAB4QiEfiAQB4AAAAAAAAAJBIAB4QiEfiAQB4AAAAAAAAAEAQAB4QiEfiAQB4AAAAAAAAASCQABgEAgEAgEBwAAAAAAAAAMCQABgEAgEAgEBwAAAAAAAAAIAgABgEAgEAgEBwAAAAAAJBIAB4QiEQj8QiEQiEAAAAAAGBIGB4QiEQj8QiEQiEAAAAAACAgAD8QCAQDwQCAQD8AAAAAAAAAAAAADYEjknkgkDYAAAAAAAAAfkgkEg/EgkEgkE8AAAAAAAAAGBIAB4QiEQiEQh4AAAAAAAAAJBIAB4QiEQiEQh4AAAAAAAAAEAQAB4QiEQiEQh4AAAAAAAAAGBIACEQiEQiEQh8AAAAAAAAAEAQACEQiEQiEQh8AAAAAAAAAJBIACEQiEQiEQh8AgEPAAJBIAB4QiEQiEQiEQh4AAAAAAJBIACEQiEQiEQiEQh4AAAAAAAAAAAgED4kkgkEgkj4EAgAAAAAAGBIIBAeBAIBAIj8AAAAAAAAAgkERBQED4ED4EAgAAAAAAAAA8EQiEQ9EIjkIhEEAAAAAAAAADAkEAgfAgEAgEAgEEgYAAAAACAgAB4Ah8QiEQh8AAAAAAAAACAgABgEAgEAgEBwAAAAAAAAACAgAB4QiEQiEQh4AAAAAAAAACAgACEQiEQiEQh8AAAAAAAAAMiYAD4QiEQiEQiEAAAAAAMiYACEQjEUiURiEQiEAAAAAAABwBB4RB4AD4AAAAAAAAAAAAABwRCIRBwAD4AAAAAAAAAAAAAAAEAgAAgEBAQiEQh4AAAAAAAAAAAAAD8QCAQAAAAAAAAAAAAAAAAAAD8AgEAgAAAAAAAAAAABAYBAIhICAgICYkgICA8AAAABAYBAIhICAgIiMig8AgEAAAAAAEAgAAgEAgEAgEAgAAAAAAAAAAAAAAkJCQkCQJAkAAAAAAAAAAAAAEgSBIEhISEgAAAAAAiBEiBEiBEiBEiBEiBEiBEiBEqiqqiqqiqqiqqiqqiqqiqqiq7l27l27l27l27l27l27l27l2EAgEAgEAgEAgEAgEAgEAgEAgEAgEAgEAgEHgEAgEAgEAgEAgEAgEAgEAg8Ag8AgEAgEAgEAgKBQKBQKBQKHQKBQKBQKBQKBQAAAAAAAAAAHwKBQKBQKBQKBQAAAAAAAAA8Ag8AgEAgEAgEAgKBQKBQKBQ6AQ6BQKBQKBQKBQKBQKBQKBQKBQKBQKBQKBQKBQAAAAAAAAA+AQ6BQKBQKBQKBQKBQKBQKBQ6AQ+AAAAAAAAAAAKBQKBQKBQKHwAAAAAAAAAAAAEAgEAgEAg8Ag8AAAAAAAAAAAAAAAAAAAAAHgEAgEAgEAgEAgEAgEAgEAgEA/AAAAAAAAAAAAEAgEAgEAgEH/AAAAAAAAAAAAAAAAAAAAAAH/EAgEAgEAgEAgEAgEAgEAgEA/EAgEAgEAgEAgAAAAAAAAAAH/AAAAAAAAAAAAEAgEAgEAgEH/EAgEAgEAgEAgEAgEAgEAgH4gH4gEAgEAgEAgKBQKBQKBQKBfKBQKBQKBQKBQKBQKBQKBQL5AP4AAAAAAAAAAAAAAAAAAAP5AL5QKBQKBQKBQKBQKBQKBQ74A/4AAAAAAAAAAAAAAAAAAA/4A75QKBQKBQKBQKBQKBQKBQL5AL5QKBQKBQKBQAAAAAAAAA/4A/4AAAAAAAAAAKBQKBQKBQ74A75QKBQKBQKBQEAgEAgEAg/4A/4AAAAAAAAAAKBQKBQKBQKH/AAAAAAAAAAAAAAAAAAAAA/4A/4gEAgEAgEAgAAAAAAAAAAH/KBQKBQKBQKBQKBQKBQKBQKB/AAAAAAAAAAAAEAgEAgEAgH4gH4AAAAAAAAAAAAAAAAAAAH4gH4gEAgEAgEAgAAAAAAAAAAB/KBQKBQKBQKBQKBQKBQKBQKH/KBQKBQKBQKBQEAgEAgEAg/4g/4gEAgEAgEAgEAgEAgEAgEHgAAAAAAAAAAAAAAAAAAAAAAA/EAgEAgEAgEAg////////////////////////AAAAAAAAAAAA////////////8Hg8Hg8Hg8Hg8Hg8Hg8Hg8HgD4fD4fD4fD4fD4fD4fD4fD4f////////////AAAAAAAAAAAAAAAAAAAB0RiIRCIRh0AAAAAAAAAOCIRCQfCEQiEQj4QCAQAAAAAfiAQCAQCAQCAQCAAAAAAAAAAAAAAD8QiEQiEQiEAAAAAAAAAfiAIAgCAQEBAQD8AAAAAAAAAAAAAB8RCIRCIRBwAAAAAAAAAAAAACEQiEQiERj0QCAQAAAAAAAAAH8EAgEAgEAYAAAAAAAAAED4kkkkkkkkkfAgAAAAAAAAAPCEQiEWiEQiEQh4AAAAAAAAAPCEQiEQiEQhIJDMAAAAAAAAAPggCB4QiEQiEQh4AAAAAAAAAAAAADYkkkkjYAAAAAAAAAAAAAgIfEUkkkoj4QEAAAAAAAAAAAAAHhAQD8QBAHgAAAAAAAAAAAAAPCEQiEQiEQiEAAAAAAAAAAAAfgAAD8AAAfgAAAAAAAAAAAAAAAgED4EAgAD4AAAAAAAAAABAEAQBAQEBAAD4AAAAAAAAAAAICAgIAgCAIAB8AAAAAAAAADAkEggEAgEAgEAgEAgEAgEAgEAgEAgEAgEEgkDAAAAAAAAAAAAAEAgAD4AAgEAAAAAAAAAAAAAAABkTAAMiYAAAAAAAAAAAwJBIGAAAAAAAAAAAAAAAAAAAAAAAAAAAAwGAAAAAAAAAAAAAAAAAAAAAAgEAAAAAAAAAAAAAMBAIBAIRCIRBIFAYAAAAAAABwJBIJBIAAAAAAAAAAAAAAAAAwJAQEB4AAAAAAAAAAAAAAAAAAAAAAB4PB4PB4PAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            },
            "turkish": {
                "width": 9,
                "height": 16,
                "data": "AAAAAAAAAAAAAAAAAAAAAAAAAAAfkCpUCgV6mUCgT8AAAAAAAAAfn+23+/2G53+/z8AAAAAAAAAAAAbH8/n8/j4OAgAAAAAAAAAAAAEBwfH8fBwEAAAAAAAAAAAAAwPB453O5wwGB4AAAAAAAAAAAwPD8/3+fgwGB4AAAAAAAAAAAAAAAGB4PAwAAAAAAAAA/3+/3+/3+52Gw3O/3+/3+/3+AAAAAAAB4ZiEQjMPAAAAAAAA/3+/3+/2GmV6vUyw3+/3+/3+AAAHgcGhkeGYzGYzDwAAAAAAAAAPDMZjMZh4GD8GAwAAAAAAAAAPxmPxgMBgMDg8HAAAAAAAAAAfzGfzGYzGYzO53MwAAAAAAAAAAwGG2PHOPG2GAwAAAAAAAEAwHA8Hw/nw8HAwEAAAAAAAAAEBgcHh8/h8HgcBgEAAAAAAAAAGB4fgwGAwfh4GAAAAAAAAAAAZjMZjMZjMZgAZjMAAAAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAAAAA/n8/n8AAAAAAAAAGB4fgwGAwfh4GD8AAAAAAAAAGB4fgwGAwGAwGAwAAAAAAAAAGAwGAwGAwGD8PAwAAAAAAAAAAAAAAwDH8DAwAAAAAAAAAAAAAAAABgYH8YBgAAAAAAAAAAAAAAAAAAwGAwH8AAAAAAAAAAAAAAAABQbH8bBQAAAAAAAAAAAAAAAEBwOD4fH8/gAAAAAAAAAAAAA/n8fD4OBwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGB4PB4GAwGAAGAwAAAAAAADMZjMJAAAAAAAAAAAAAAAAAAAAADYbH8bDYbH8bDYAAAAAAGAwfGMwmAfAMBkMxj4GAwAAAAAAAAAwmMDAwMDAxkMAAAAAAAAAODYbBwdm4zGYzDsAAAAAAABgMBgYAAAAAAAAAAAAAAAAAAAADAwMBgMBgMBgGAYAAAAAAAAAMAwDAYDAYDAYGBgAAAAAAAAAAAAADMPH+PDMAAAAAAAAAAAAAAAAAwGD8GAwAAAAAAAAAAAAAAAAAAAAAAAwGAwMAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAAAAAAAAAAGAwAAAAAAAAAAAAAgMDAwMDAwEAAAAAAAAAAODYxmM1msxmMbBwAAAAAAAAAGBweAwGAwGAwGD8AAAAAAAAAfGMBgYGBgYGAxn8AAAAAAAAAfGMBgMPAMBgMxj4AAAAAAAAADA4PDYzH8DAYDA8AAAAAAAAA/mAwGA/AMBgMxj4AAAAAAAAAODAwGA/GMxmMxj4AAAAAAAAA/mMBgMDAwMBgMBgAAAAAAAAAfGMxmMfGMxmMxj4AAAAAAAAAfGMxmMfgMBgMDDwAAAAAAAAAAAAGAwAAAAAwGAAAAAAAAAAAAAAGAwAAAAAwGBgAAAAAAAAAAAMDAwMDAMAwDAMAAAAAAAAAAAAAD8AAAfgAAAAAAAAAAAAAADAMAwDAMDAwMDAAAAAAAAAAfGMxgYGAwGAAGAwAAAAAAAAAAD4xmM3m83m4wD4AAAAAAAAAEBwbGMxn8xmMxmMAAAAAAAAA/DMZjMfDMZjMZn4AAAAAAAAAPDMwmAwGAwGEZh4AAAAAAAAA+DYZjMZjMZjMbHwAAAAAAAAA/jMYjQeDQYDEZn8AAAAAAAAA/jMYjQeDQYDAYHgAAAAAAAAAPDMwmAwG8xmMZh0AAAAAAAAAxmMxmM/mMxmMxmMAAAAAAAAAPAwGAwGAwGAwGB4AAAAAAAAAHgYDAYDAYzGYzDwAAAAAAAAA5jMZjYeDwbDMZnMAAAAAAAAA8DAYDAYDAYDEZn8AAAAAAAAAxnc/n81mMxmMxmMAAAAAAAAAxnM9n83mcxmMxmMAAAAAAAAAfGMxmMxmMxmMxj4AAAAAAAAA/DMZjMfDAYDAYHgAAAAAAAAAfGMxmMxmMxms3j4DAcAAAAAA/DMZjMfDYZjMZnMAAAAAAAAAfGMxjAOAYBmMxj4AAAAAAAAAfj8WgwGAwGAwGB4AAAAAAAAAxmMxmMxmMxmMxj4AAAAAAAAAxmMxmMxmMxjYOAgAAAAAAAAAxmMxmM1ms1n87jYAAAAAAAAAxmMbD4OBwfDYxmMAAAAAAAAAZjMZjMPAwGAwGB4AAAAAAAAA/mMhgYGBgYGExn8AAAAAAAAAPBgMBgMBgMBgMB4AAAAAAAAAAEAwHAcBwHAcBgEAAAAAAAAAPAYDAYDAYDAYDB4AAAAAAEBwbGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+AAAABgGAYAAAAAAAAAAAAAAAAAAAAAAAAADwDD4zGYzDsAAAAAAAAA4DAYDwbDMZjMZj4AAAAAAAAAAAAAD4xmAwGAxj4AAAAAAAAAHAYDB4bGYzGYzDsAAAAAAAAAAAAAD4xn8wGAxj4AAAAAAAAAHBsMhgeBgMBgMDwAAAAAAAAAAAAADszGYzGYzD4DGYeAAAAA4DAYDYdjMZjMZnMAAAAAAAAAGAwABwGAwGAwGB4AAAAAAAAABgMAAcBgMBgMBgMZjMPAAAAA4DAYDMbDweDYZnMAAAAAAAAAOAwGAwGAwGAwGB4AAAAAAAAAAAAAHY/ms1ms1mMAAAAAAAAAAAAAG4ZjMZjMZjMAAAAAAAAAAAAAD4xmMxmMxj4AAAAAAAAAAAAAG4ZjMZjMZj4YDA8AAAAAAAAADszGYzGYzD4DAYHgAAAAAAAAG4djMYDAYHgAAAAAAAAAAAAAD4xjAOAYxj4AAAAAAAAAEBgMH4MBgMBgNg4AAAAAAAAAAAAAGYzGYzGYzDsAAAAAAAAAAAAAGMxmMxmMbBwAAAAAAAAAAAAAGMxms1ms/jYAAAAAAAAAAAAAGMbBwOBwbGMAAAAAAAAAAAAAGMxmMxmMxj8BgY+AAAAAAAAAH8zAwMDAxn8AAAAAAAAADgwGAwcAwGAwGAcAAAAAAAAAGAwGAwGAwGAwGAwAAAAAAAAAcAwGAwDgwGAwGDgAAAAAAADs3AAAAAAAAAAAAAAAAAAAAAAAAAAEBwbGMxmM/gAAAAAAAAAAPDMwmAwGAwGEZh4GBgAAAAAAzAAAGYzGYzGYzDsAAAAAAAAYGBgAD4xn8wGAxj4AAAAAAAAgODYADwDD4zGYzDsAAAAAAAAAzAAADwDD4zGYzDsAAAAAAADAMAwADwDD4zGYzDsAAAAAAABwbBwADwDD4zGYzDsAAAAAAAAAAAAAD4xmAwGAxj4GBgAAAAAgODYAD4xn8wGAxj4AAAAAAAAAxgAAD4xn8wGAxj4AAAAAAADAMAwAD4xn8wGAxj4AAAAAAAAAZgAABwGAwGAwGB4AAAAAAAAwPDMABwGAwGAwGB4AAAAAAAAAAAAABwGAwGAwGB4AAAAAAAGMAAgODYxmM/mMxmMAAAAAAODYOAgODYxn8xmMxmMAAAAAADAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAGYdhsfmw2DcAAAAAAAAAPjYzGY/mYzGYzGcAAAAAAAAgODYAD4xmMxmMxj4AAAAAAAAAxgAAD4xmMxmMxj4AAAAAAADAMAwAD4xmMxmMxj4AAAAAAABgeGYAGYzGYzGYzDsAAAAAAADAMAwAGYzGYzGYzDsAAAAAAAAwAB4GAwGAwGAwGB4AAAAAAAGMAD4xmMxmMxmMxj4AAAAAAAGMAGMxmMxmMxmMxj4AAAAAAAAAAAAAD4zm89nMxj4AAAAAAABwbDIYHgYDAYDA5n4AAAAAAAAAfGMxmc3ns5mMxj4AAAAAAAAAfGMxjAOAYBmMxj4GBgAAAAAAAAAAD4xjAOAYxj4GBgAAAAAwMDAADwDD4zGYzDsAAAAAAAAYGBgABwGAwGAwGB4AAAAAAAAwMDAAD4xmMxmMxj4AAAAAAAAwMDAAGYzGYzGYzDsAAAAAAAAAdm4AG4ZjMZjMZjMAAAAAAdm4AGM5ns/m8zmMxmMAAAAAAADMfh4ZmEwGA3mMbh0AAAAAAAAAzDwADszGYzGYzD4DGYeAAAAAMBgABgMDAwGMxj4AAAAAAAAAfEEslUslUqkEfAAAAAAAAAAAAAAAAA/gMBgMBgAAAAAAAADA4DEZjYGBgYG4hgYGB8AAAADA4DEZjYGBgZmcmh+BgMAAAAAAGAwAAwGAwPB4PAwAAAAAAAAAAAAABsbGwbBsAAAAAAAAAAAAAAAAGwbBsbGwAAAAAAAAAESIESIESIESIESIESIESIESIVVUVVUVVUVVUVVUVVUVVUVVU3Tu3Tu3Tu3Tu3Tu3Tu3Tu3TuGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGAwGHwGAwGAwGAwGAwYGAEBwbGMxn8xmMxmMAAAAAAfGMEBwbGMxn8xmMxmMAAAAAADAMEBwbGMxn8xmMxmMAAAAAAAAAfEEmlEolEmkEfAAAAAAAANhsNhsNnsBnsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsNhsAAAAAAAH8BnsNhsNhsNhsNhsNhsNhsNnsBn8AAAAAAAAAAAAAAAGAwfGMwGAxj4GAwAAAAAAAAAADMZh4GD8GD8GAwAAAAAAAAAAAAAAAAHwGAwGAwGAwGAwGAwGAwGAwGA/AAAAAAAAAAAAGAwGAwGAwGH/AAAAAAAAAAAAAAAAAAAAAAH/GAwGAwGAwGAwGAwGAwGAwGA/GAwGAwGAwGAwAAAAAAAAAAH/AAAAAAAAAAAAGAwGAwGAwGH/GAwGAwGAwGAwAAAdm4ADwDD4zGYzDsAAAAAAdm4ABwbGMxn8xmMxmMAAAAAANhsNhsNhvMB/AAAAAAAAAAAAAAAAAAAB/MBvNhsNhsNhsNhsNhsNhsNnvAH/AAAAAAAAAAAAAAAAAAAH/AHvNhsNhsNhsNhsNhsNhsNhvMBvNhsNhsNhsNhsAAAAAAAH/AH/AAAAAAAAAAAANhsNhsNnvAHvNhsNhsNhsNhsAAAAAAxj4xmMxmMfGMAAAAAAAAAODYbBwAD4AAAAAAAAAAAAAAAPDYbB8AD8AAAAAAAAAAAAODYAH8ZjEaDwaDEZn8AAAAAAAGMAH8ZjEaDwaDEZn8AAAAAAMAwAH8ZjEaDwaDEZn8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAwAB4GAwGAwGAwGB4AAAAAAPDMAB4GAwGAwGAwGB4AAAAAAADMAB4GAwGAwGAwGB4AAAAAAGAwGAwGAwGHwAAAAAAAAAAAAAAAAAAAAAAA/GAwGAwGAwGAw////////////////////////AAAAAAAAAAH/////////////AAwGAwGAwAAAGAwGAwGAAAAAMAwAB4GAwGAwGAwGB4AAAAAA//////////4AAAAAAAAAAAAAGBgAD4xmMxmMxmMxj4AAAAAAAAAeGYzGY2GYxmMxmYAAAAAAODYAD4xmMxmMxmMxj4AAAAAAMAwAD4xmMxmMxmMxj4AAAAAAAAAdm4AD4xmMxmMxj4AAAAAAdm4AD4xmMxmMxmMxj4AAAAAAAAAAAAADMZjMZjMZj4YDAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGMbBwODYxgAAAAAAAGBgAGMxmMxmMxmMxj4AAAAAAODYAGMxmMxmMxmMxj4AAAAAAMAwAGMxmMxmMxmMxj4AAAAAAADAMAwABwGAwGAwGB4AAAAAAAAAxgAAGMxmMxmMxj8BgYeAAAH+AAAAAAAAAAAAAAAAAAAAAAAYGBgAAAAAAAAAAAAAAAAAAAAAAAAAAAAH8AAAAAAAAAAAAAAAAAAGAwfgwGAAAD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAMDENnYGBgZmcmh+BgMAAAAAAf22222ew2Gw2Gw2AAAAAAAD4xjAODYxmMbBwDGMfAAAAAAAAAAAAAwAD8AAwAAAAAAAAAAAAAAAAAAAAAAAAAAwDDwAAAABwbDYOAAAAAAAAAAAAAAAAAAGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAwOAwGAwPAAAAAAAAAAAAAAAD4Bh4BgMfAAAAAAAAAAAAAAAB4ZgYGBkfgAAAAAAAAAAAAAAAAAAAfj8fj8fj8fgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "amigaFont": false
            }
        };

        BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";

        fontBitsBuffer = {};

        // Receives an RGBA image, <rgbaSource>, and the font width <fontWidth>, and delivers a double-scaled version, suitable for retina-type devices.
        function doubleScale(rgbaSource, fontWidth) {
            var byteWidth, doubledByteWidth, rgba, rgbaDoubled, startOfRow, i, k;
            byteWidth = fontWidth * 4;
            doubledByteWidth = byteWidth * 2;
            rgbaDoubled = new Uint8Array(rgbaSource.length * 4);
            for (i = 0, k = 0; i < rgbaSource.length; i += 4) {
                rgba = rgbaSource.subarray(i, i + 4);
                rgbaDoubled.set(rgba, k);
                k += 4;
                rgbaDoubled.set(rgba, k);
                k += 4;
                if ((i + 4) % byteWidth === 0) {
                    startOfRow = k - doubledByteWidth;
                    rgbaDoubled.set(rgbaDoubled.subarray(startOfRow, startOfRow + doubledByteWidth), k);
                    k += doubledByteWidth;
                }
            }
            return rgbaDoubled;
        }

        // Returns properties that describe a font's size, and functions which return RGBA arrays, which are to be inserted in an entire RGBA image. Accepts <bits> an array of boolean values which describe a 1-bit image of a font, all 256 characters, as well as the <width> and <height> of each glyph, and a boolean, <amigaFont>, which if set to true is used when drawing a glyph in bold type.
        function font(bits, width, height, amigaFont, options) {
            // <fontBitWidth> is the size of each glyph, in amount of bits, <fontBuffer> is used to buffer RGBA images of each glyph. <fontBuffer24Bit> is used on a case-by-case basis when rendering a glyph in the get24BitData() function.
            var fontBitWidth, fontBuffer, fontBuffer24Bit, excludeNinthBit;
            fontBitWidth = width * height;
            fontBuffer = [];
            // Set <excludeNinthBit> to true, if we need to ignore the ninth bit of a font.
            excludeNinthBit = (width === 9 && options.bits !== "9") || (width === 9 && options.thumbnail);
            // RGBA data, requires Red, Green, Blue, and Alpha values for each 'bit' in the 1-bit image data, <bits>.
            fontBuffer24Bit = new Uint8Array((excludeNinthBit ? width - 1 : width) * height * 4);

            // Accepts a character code <charCode>, e.g. 65 = A, with an array of RGBA values, <palette>, and a foreground, <fg>, and background, <bg>, value which points at an element in the array.
            function getData(charCode, palette, fg, bg) {
                var i, j, k, bufferIndex;
                // For each value of <charCode>, and <fg>, and <bg>, create a unique reference for our buffered array, <fontBuffer>.
                bufferIndex = charCode + (fg << 8) + (bg << 12);
                // If we haven't already drawn this glyph before...
                if (!fontBuffer[bufferIndex]) {
                    // ... create a new one.
                    fontBuffer[bufferIndex] = new Uint8Array((excludeNinthBit ? width - 1 : width) * height * 4);
                    // Works through each bit in <bits> at the point where our <charCode> starts, and copy <fg> where the bit is set, and <bg> where it is not.
                    for (i = 0, j = charCode * fontBitWidth, k = 0; i < fontBitWidth; ++i, ++j) {
                        // Ignore the ninth bit, if <excludeNinthBit> is set.
                        if (!excludeNinthBit || (i + 1) % 9 !== 0) {
                            if (bits[j]) {
                                fontBuffer[bufferIndex].set(palette[fg], k);
                            } else {
                                // In case that this is an <amigaFont>, and the foreground colour <fg> is set to bold type, i.e. 8 to 15, make sure we 'double-width' the glyph.
                                if (amigaFont && (fg > 7) && (i % width > 0) && bits[j - 1] && (options.bits === "ced" || options.bits === "workbench")) {
                                    fontBuffer[bufferIndex].set(palette[fg], k);
                                } else {
                                    fontBuffer[bufferIndex].set(palette[bg], k);
                                }
                            }
                            k += 4;
                        }
                    }
                    if (options["2x"]) {
                        fontBuffer[bufferIndex] = doubleScale(fontBuffer[bufferIndex], excludeNinthBit ? width - 1 : width);
                    }
                }
                // Return the buffered RGBA image.
                return fontBuffer[bufferIndex];
            }

            // Same as getData(), but accepts only a <fg> (foreground) and <bg> (background) arrays as RGBA data. Returns, as with getData(), raw RGBA data which describes the glyph's image.
            function get24BitData(charCode, fg, bg) {
                var i, j, k;
                for (i = 0, j = charCode * fontBitWidth, k = 0; i < fontBitWidth; ++i, ++j) {
                    // Ignore the ninth bit, if <excludeNinthBit> is set.
                    if (!excludeNinthBit || (i + 1) % 9 !== 0) {
                        if (bits[j]) {
                            fontBuffer24Bit.set(fg, k);
                        } else {
                            fontBuffer24Bit.set(bg, k);
                        }
                        k += 4;
                    }
                }
                if (options["2x"]) {
                    return doubleScale(fontBuffer24Bit, excludeNinthBit ? width - 1 : width);
                }
                return fontBuffer24Bit;
            }

            // Entrypoint for each of the functions publicly available in Font.
            return {
                "getData": getData,
                "get24BitData": get24BitData,
                "height": height * (options["2x"] ? 2 : 1),
                "width" : (excludeNinthBit ? 8 : width) * (options["2x"] ? 2 : 1)
            };
        }

        // Converts a stream of bytes returned by a File object, <file>, into a boolean array, <bits>, which represent the 1-bit image data of all the glyphs. The number of bytes to be read are calculated by the <width> and <height> specified for each glyph.
        function bytesToBits(file, width, height) {
            var bits, i, j, k, v;
            // Build the <bits> array, for all 256 glyphs.
            bits = new Uint8Array(width * height * 256);
            for (i = width * height * 256 / 8, k = 0; i > 0; --i) {
                v = file.get();
                for (j = 7; j >= 0; --j) {
                    // returns true or false if the bit is set for each bit in every byte read.
                    bits[k++] = !!((v >> j) & 1);
                }
            }
            return bits;
        }

        // Converts a string of <text> in Base64 characters to a File object. This is probably much slower than calling window.atob(), but atob() cannot be invoked by a Web Worker instance. Truncating the array based on padding characters is not implemented, but is not necessary for this script. <bytes16> is used on the assumption that keeping the bit-shifting limited to typed-arrays is faster that dynamic types.
        function base64ToFile(text) {
            var i, j, bytes16, bytes8;
            bytes16 = new Uint32Array(1);
            bytes8 = new Uint8Array(text.length / 4 * 3);
            for (i = j = 0; i < text.length; bytes16[0] = 0) {
                bytes16[0] += (BASE64_CHARS.indexOf(text.charAt(i++)) & 63) << 18;
                bytes16[0] += (BASE64_CHARS.indexOf(text.charAt(i++)) & 63) << 12;
                bytes16[0] += (BASE64_CHARS.indexOf(text.charAt(i++)) & 63) << 6;
                bytes16[0] += BASE64_CHARS.indexOf(text.charAt(i++)) & 63;
                bytes8[j++] = (bytes16[0] >> 16) & 255;
                bytes8[j++] = (bytes16[0] >> 8) & 255;
                bytes8[j++] = bytes16[0] & 255;
            }
            return new File(bytes8);
        }

        // Returns a font object returned by <font> based on the data held in FONT_PRESETS using the key <name>. When the preset is called initially, the 1-bit image data returned by bytesToBits() is buffered in <fontBitsBuffer>, referenced by the key <name>, which may save some cpu cycles when the function is called again. Assumes <name> absolutely exists in FONT_PRESETS, and any error checking is handled by calling has() previously.
        function preset(name, options) {
            // Aliases for various keys, used to preserve compatibility with url schemes.
            switch (name) {
            case "amiga":
                name = "topaz";
                break;
            case "microknightplus":
                name = "microknight+";
                break;
            case "topazplus":
                name = "topaz+";
                break;
            case "topaz500plus":
                name = "topaz500+";
                break;
            }
            // If we haven't already converted this data to a boolean array...
            if (!fontBitsBuffer[name]) {
                // ... build and store it.
                fontBitsBuffer[name] = bytesToBits(base64ToFile(FONT_PRESETS[name].data), FONT_PRESETS[name].width, FONT_PRESETS[name].height);
            }
            // Return our font object based on the buffered array by calling font() with all the data held in FONT_PRESETS.
            return font(fontBitsBuffer[name], FONT_PRESETS[name].width, FONT_PRESETS[name].height, FONT_PRESETS[name].amigaFont, options);
        }

        // Returns a font object by reading <file>, assuming a predefined glyph height, <fontHeight>. This is a predefined function to handle font data held in xbin files.
        function xbin(file, fontHeight, options) {
            return font(bytesToBits(file, 8, fontHeight), 8, fontHeight, false, options);
        }

        // A generic function, leveraged by various parsers to read font data of a standard 8x16 size, to be read from <file>, and returns a font object.
        function font8x16x256(file, options) {
            return font(bytesToBits(file, 8, 16), 8, 16, false, options);
        }

        // A simple function, which returns true or false depending on whether <name> is a key name in FONT_PRESETS, so that a call to preset will return valid data.
        function has(name) {
            switch (name) {
            case "amiga":
            case "microknightplus":
            case "topazplus":
            case "topaz500plus":
                return true;
            default:
                return FONT_PRESETS.hasOwnProperty(name);
            }
        }

        // Entrypoint for publicly-available functions.
        return {
            "preset": preset,
            "xbin": xbin,
            "font8x16x256": font8x16x256,
            "has": has
        };
    }());

    // Collects together several functions and variables which hold palette data.
    Palette = (function () {
        // Variables, which should be treated as constants for use when rendering .asc, .ans, .bin files, as well as when setting "bits" to "ced", and "workbench". All are defined as native arrays of RGBA data, held as Uint8Array arrays. e.g. [[0, 0, 0, 255], [255, 255, 255,255] ...]
        var ASC_PC, ANSI, BIN, CED, WORKBENCH;

        // Converts a 6-bit <value>, representing a colour in the EGA palette, to its RGBA equivalent (as a Uint8Array).
        function egaRGB(value) {
            return new Uint8Array([
                (((value & 32) >> 5) + ((value & 4) >> 1)) * 0x55,
                (((value & 16) >> 4) + ((value & 2))) * 0x55,
                (((value & 8) >> 3) + ((value & 1) << 1)) * 0x55,
                255
            ]);
        }

        // Define the various preset palettes. Since the Workbench palette does not have equivalent EGA values, RGBA values are defined directly.
        ASC_PC = [0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7].map(egaRGB);
        ANSI = [0, 4, 2, 20, 1, 5, 3, 7, 56, 60, 58, 62, 57, 61, 59, 63].map(egaRGB);
        BIN = [0, 1, 2, 3, 4, 5, 20, 7, 56, 57, 58, 59, 60, 61, 62, 63].map(egaRGB);
        CED = [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0].map(egaRGB);
        WORKBENCH = [new Uint8Array([170, 170, 170, 255]), new Uint8Array([170, 170, 170, 255]), new Uint8Array([0, 0, 0, 255]), new Uint8Array([0, 0, 0, 255]), new Uint8Array([255, 255, 255, 255]), new Uint8Array([255, 255, 255, 255]), new Uint8Array([102, 136, 187, 255]), new Uint8Array([102, 136, 187, 255]), new Uint8Array([0, 0, 255, 255]), new Uint8Array([0, 0, 255, 255]), new Uint8Array([255, 0, 255, 255]), new Uint8Array([255, 0, 255, 255]), new Uint8Array([0, 255, 255, 255]), new Uint8Array([0, 255, 255, 255]), new Uint8Array([255, 255, 255, 255]), new Uint8Array([255, 255, 255, 255])];

        // Reads palette information from <file>, assuming it is held as RGB data, and has 16 members. Returns a native array of RGBA data, held as Uint8Array arrays.
        function triplets16(file) {
            var pal, i, r, g, b;
            for (pal = [], i = 0; i < 16; ++i) {
                r = file.get();
                g = file.get();
                b = file.get();
                pal.push(new Uint8Array([r << 2 | r >> 4, g << 2 | g >> 4, b << 2 | b >> 4, 255]));
            }
            return pal;
        }

        // A very specific function to interpret palette information held by adf files. Information on all 64 colours is read from <file>, and then only colours from specific places in that array are used in the image. Returns RGBA data in the same format returned by triplets16().
        function adf(file) {
            var pal, i, r, g, b;
            for (pal = [], i = 0; i < 64; ++i) {
                r = file.get();
                g = file.get();
                b = file.get();
                pal.push(new Uint8Array([r << 2 | r >> 4, g << 2 | g >> 4, b << 2 | b >> 4, 255]));
            }
            return [pal[0], pal[1], pal[2], pal[3], pal[4], pal[5], pal[20], pal[7], pal[56], pal[57], pal[58], pal[59], pal[60], pal[61], pal[62], pal[63]];
        }

        // Entrypoint for the various public methods.
        return {
            "ASC_PC": ASC_PC,
            "ANSI": ANSI,
            "BIN": BIN,
            "CED": CED,
            "WORKBENCH": WORKBENCH,
            "adf": adf,
            "triplets16": triplets16
        };
    }());

    // Scales the RGBA image data, <sourcedata>, by averaging each "chunk" of a certain size, <chunkWidth> and <chunkHeight>. <width> and <height> describe the size of the source image.
    function scaleCanvas(sourceData, width, height, chunkWidth, chunkHeight, options) {
        var destWidth, destHeight, destData, rgba, pixelRowOffset, chunkSize, i, j, k, x, y, r, g, b, a;

        // Temporary var for storing the value of the averaged "chunk".
        rgba = new Uint8Array(4);

        // Define the size of the destination image...
        destWidth = width / chunkWidth;
        destHeight = height / chunkHeight;
        // ... and create an 8-bit array for its RGBA data.
        destData = new Uint8Array(destWidth * destHeight * 4);

        // Pre-calculations used when building the destination data.
        pixelRowOffset = (width - chunkWidth) * 4;
        chunkSize = chunkWidth * chunkHeight;

        for (i = x = y = 0; i < destData.length; i += 4) {
            for (j = r = g = b = a = 0, k = (y * width * chunkHeight + x * chunkWidth) * 4; j < chunkSize; ++j) {
                // Add all the values in each "chunk" for red, green, blue, and alpha bytes.
                r += sourceData[k++];
                g += sourceData[k++];
                b += sourceData[k++];
                a += sourceData[k++];
                // Seek the next row of pixels in each "chunk".
                if ((j + 1) % chunkWidth === 0) {
                    k += pixelRowOffset;
                }
            }
            // Average out the values for each pixel in the destination image.
            rgba[0] = Math.round(r / chunkSize);
            rgba[1] = Math.round(g / chunkSize);
            rgba[2] = Math.round(b / chunkSize);
            rgba[3] = Math.round(a / chunkSize);
            // Write our averaged pixel.
            destData.set(rgba, i);
            if (++x === destWidth) {
                x = 0;
                ++y;
            }
        }

        // Returns the <width> and <height> of the destination image, as well as its RGBA data, <rgbaData>.
        return {
            "width": destWidth,
            "height": destHeight,
            "rgbaData": destData,
            "2x": options["2x"]
        };
    }

    // Receives a <raw> object returned from the image-parsing functions found in Parser, and outputs a Uint8Array with RGBA data, <rgbaData>, with dimensions <width> and <height>. <start> and <length> point to rows offsets, so that only part of the image can be rendered. <altFont> is a font object, returned by font() to be used when rendering the image (assuming no font information is held in raw.font), and <options>, which are passed by the user.
    function display(raw, start, length, options) {
        var canvasWidth, canvasHeight, rgbaData, end, i, k, l, x, fontBitWidth, fontData, rowOffset, data, screenOffset, fontOffset, chunky;

        // Temporary variable to pre-calculate some data.
        fontBitWidth = raw.font.width * 4;

        data = raw.getData();

        // Define where to stop reading data.
        start = start * raw.columns * 10;
        end = Math.min(start + length * raw.columns * 10, data.length);

        // Calculate the dimensions of the output image.
        canvasWidth = raw.columns * raw.font.width;
        canvasHeight = (end - start) / (raw.columns * 10) * raw.font.height;

        // Initialize the RGBA image data and calculate how many bytes are in each text-row.
        rgbaData = new Uint8Array(canvasWidth * canvasHeight * 4);
        rowOffset = canvasWidth * 4;

        for (i = start, screenOffset = 0, x = 0; i < end; i += 10, screenOffset += fontBitWidth) {
            // If we have 24 bit data
            if (data[i + 1]) {
                fontData = raw.font.get24BitData(data[i], data.subarray(i + 2, i + 6), data.subarray(i + 6, i + 10));
            } else {
                fontData = raw.font.getData(data[i], raw.palette, data[i + 2], data[i + 3]);
            }
            for (fontOffset = screenOffset, k = l = 0; k < raw.font.height; ++k, fontOffset += rowOffset, l += fontBitWidth) {
                rgbaData.set(fontData.subarray(l, l + fontBitWidth), fontOffset);
            }
            if (++x % raw.columns === 0) {
                screenOffset += (raw.font.height - 1) * rowOffset;
            }
        }

        // Finally, if the "thumbnail" option is chosen...
        if (options.thumbnail) {
            // ... calculate the scale factor and return the reduced image data.
            chunky = Math.pow(2, 4 - options.thumbnail);
            return scaleCanvas(rgbaData, canvasWidth, canvasHeight, chunky, chunky, options);
        }

        // Return the imageData, as a Uint8Array RGBA array, <rgbaData>, with image dimensions, <width> and <height>.
        return {
            "width": canvasWidth,
            "height": canvasHeight,
            "rgbaData": rgbaData,
            "2x": options["2x"]
        };
    }

    // A simple function to return a CANVAS element, at the defined <width> and <height>.
    function createCanvas(width, height) {
        var canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        return canvas;
    }

    // Converts data returned by display() as a canvas element, can also be called externally after the results of a Web Worker has been returned (as creating a canvas element is not possible in a Worker thread).
    function displayDataToCanvas(displayData) {
        var canvas, ctx, imageData;
        canvas = createCanvas(displayData.width, displayData.height);
        ctx = canvas.getContext("2d");
        imageData = ctx.createImageData(canvas.width, canvas.height);
        imageData.data.set(displayData.rgbaData, 0);
        ctx.putImageData(imageData, 0, 0);
        // Deal with pixel ratio for retina-type displays.
        if (displayData["2x"]) {
            canvas.style.width = (canvas.width / 2) + "px";
            canvas.style.height = (canvas.height / 2) + "px";
        }
        return canvas;
    }

    // Returns an options object which has been validated to make sure all the arguments are legal, and sets defaults where missing.
    function validateOptions(options) {
        var validatedOptions;

        // Create the options object, if undefined.
        options = options || {};
        validatedOptions = {};
        // "icecolors", must be a number, 0 or 1. Defaults to 0.
        validatedOptions.icecolors = ((typeof options.icecolors === "number") && options.icecolors >= 0 && options.icecolors <= 1) ? options.icecolors : 0;
        // "bits", must be "8", "9", "ced", or "workbench". Defaults to "8".
        switch (options.bits) {
        case "8":
        case "9":
        case "ced":
        case "workbench":
            validatedOptions.bits = options.bits;
            break;
        default:
            validatedOptions.bits = "8";
        }
        // "columns" setting, must be a number greater than 0. Defaults to 160.
        validatedOptions.columns = ((typeof options.columns === "number") && options.columns > 0) ? options.columns : 160;
        // "font" setting, must be a string, and be in the list of available presets. Defaults to "80x25".
        validatedOptions.font = ((typeof options.font === "string") && Font.has(options.font)) ? options.font : "80x25";
        // "thumnail", must be a number between and including 0 to 3. Defaults to 0.
        validatedOptions.thumbnail = ((typeof options.thumbnail === "number") && options.thumbnail >= 0 && options.thumbnail <= 3) ? options.thumbnail : 0;
        // "2x", must be a number, 0 or 1. Defaults to 0.
        validatedOptions["2x"] = ((typeof options["2x"] === "number") && options["2x"] >= 0 && options["2x"] <= 1) ? options["2x"] : 0;
        // "imagedata", must be 0 or 1. Defaults to 0.
        validatedOptions.imagedata = ((typeof options.imagedata === "number") && options.imagedata >= 0 && options.imagedata <= 1) ? options.imagedata : 0;
        // "rows", must be a number greater than 0. Defaults to 26.
        validatedOptions.rows = ((typeof options.rows === "number") && options.rows > 0) ? options.rows : 26;
        // "2J", must be a number 0 or 1. Defaults to 1.
        validatedOptions["2J"] = ((typeof options["2J"] === "number") && options["2J"] >= 0 && options["2J"] <= 1) ? options["2J"] : 1;
        // "filetype", can be any string, since readBytes() defaults to the ANSI renderer if it is unrecognised.
        validatedOptions.filetype = (typeof options.filetype === "string") ? options.filetype : "ans";

        return validatedOptions;
    }
    // Collects all the functions which parse the supported image formats, with a single entrypoint, readBytes.
    Parser = (function () {
        // ScreenData() returns a representation of the screen with <width> columns. This is used for images with a predefined palette. i.e. all formats except Tundra.
        function ScreenData(columns) {
            // <imageData> represents a Uint8Array of the screen, two pairs of bytes represent the character code and colour attributes in the second, as also used in the .bin file format. <rows> stores the highest row number written to, and <pos> is the current cursor position represented in the <imageData> array.
            var that, imageData, pos;

            that = this;

            // Returns the ScreenData object to its initial start, used upon initialization or when a screen-clear code is issued.
            this.reset = function () {
                imageData = new Uint8Array(columns * 1000 * 10);
                pos = 0;
                that.columns = columns;
                that.rows = 0;
            };

            this.reset();

            // Extend the <imageData> array if necessary, by creating a new array with an additional 1000 rows after from the <y> position currently attempting to be written to, and copy the existing data to the start.
            function extendImageData(y) {
                var newImageData;
                newImageData = new Uint8Array(that.columns * (y + 1000) * 10 + imageData.length);
                newImageData.set(imageData, 0);
                imageData = newImageData;
            }

            // Set the character code, <charCode>, and foreground & background attribute, <attrib>, and the <x> and <y> position of the <imageData> array.
            this.set = function (x, y, charCode, trueColor, fg, bg) {
                pos = (y * that.columns + x) * 10;
                // If we see that we will be writing past the end of the array, extend the array by calling extendImageData() with the current <y> position we want to write to.
                if (pos >= imageData.length) {
                    extendImageData(y);
                }
                // Store the data...
                imageData[pos] = charCode;
                if (trueColor) {
                    // Indicate that we are referring to RGBA values...
                    imageData[pos + 1] = 1;
                    // ... and store the data.
                    imageData.set(fg, pos + 2);
                    imageData.set(bg, pos + 6);
                } else {
                    // ... and store the palette pointers.
                    imageData[pos + 2] = fg;
                    imageData[pos + 3] = bg;
                }
                // ... and update <rows> if it's the largest <y> value used so far.
                if (y + 1 > that.rows) {
                    that.rows = y + 1;
                }
            };

            this.raw = function (bytes) {
                var i, j;
                that.rows = Math.ceil(bytes.length / 2 / that.columns);
                imageData = new Uint8Array(that.columns * that.rows * 10);
                for (i = 0, j = 0; j < bytes.length; i += 10, j += 2) {
                    imageData[i] = bytes[j];
                    imageData[i + 2] = bytes[j + 1] & 15;
                    imageData[i + 3] = bytes[j + 1] >> 4;
                }
            };

            this.trimColumns = function () {
                var i, height, j, maxX, newImageData;
                for (maxX = 0, height = imageData.length / 10 / that.columns, i = 0; i < imageData.length; i += 10) {
                    // If a character code is seen, check to see if it's the highest column value, and record it if necessary.
                    if (imageData[i]) {
                        maxX = Math.max((i / 10) % that.columns, maxX);
                    }
                }
                ++maxX;
                // Create a new imageData object, with a reduced size if necessary.
                for (newImageData = new Uint8Array((maxX + 1) * height * 10), i = 0, j = 0; i < newImageData.length; i += maxX * 10, j += that.columns * 10) {
                    newImageData.set(imageData.subarray(j, j + that.columns * 10), i);
                }
                imageData = newImageData;
                // Set the new width.
                that.columns = maxX;
            };

            // Return the <imageData> array, but only up to the <rows> row.
            this.getData = function () {
                var subarray, i;
                // Before returning the truncated array, set the Alpha byte for every character position to the maximum value, otherwise the whole image will be transparent when later copying into a RGBA.
                for (subarray = imageData.subarray(0, that.columns * that.rows * 10), i = 0; i < subarray.length; i += 10) {
                    subarray[i + 5] = 255;
                    subarray[i + 9] = 255;
                }
                return subarray;
            };
        }

        // A function to parse a sequence of bytes representing an Artworx file format.
        function adf(bytes, options) {
            var file, imageData;

            // Turn bytes into a File object.
            file = new File(bytes);

            // Read version number.
            file.getC();

            imageData = new ScreenData(80);

            // Read Palette. See Palette.adf().
            imageData.palette = Palette.adf(file);
            // Read Font. See Font.font8x16x256().
            imageData.font = Font.font8x16x256(file, options);

            // Raw Imagedata.
            imageData.raw(file.read());

            // Return an object readable by display() for constructing an RGBA image.
            return {
                "imageData": imageData,
                "sauce": file.sauce // sauce record.
            };
        }

        // A function to parse a sequence of bytes representing an ANSI file format.
        function ans(bytes, options) {
            var file, escaped, escapeCode, j, code, values, columns, imageData, topOfScreen, x, y, savedX, savedY, foreground, background, foreground24bit, background24bit, drawForeground, drawBackground, bold, blink, inverse, icecolors;

            // Turn bytes into a File object.
            file = new File(bytes);

            // Reset all the attributes, used upon initialization, and on Esc[0m
            function resetAttributes() {
                foreground = 7;
                background = 0;
                foreground24bit = undefined;
                background24bit = undefined;
                bold = false;
                blink = false;
                inverse = false;
            }
            resetAttributes();

            // On the event of a new line, reset <x>, and record a new value for <topOfScreen> or <y> depending on whether the bottom of the screen has already been reached.
            function newLine() {
                x = 1;
                if (y === 26 - 1) {
                    ++topOfScreen;
                } else {
                    ++y;
                }
            }

            // Set a new position for <x> and <y>, bounded by the maxumum amount of <columns>, and rows, and the minimum amount, 1.
            function setPos(newX, newY) {
                x = Math.min(columns, Math.max(1, newX));
                y = Math.min(26, Math.max(1, newY));
            }

            // Initialize <x>, <y>, and <topOfScreen>.
            x = 1;
            y = 1;
            topOfScreen = 0;

            // Reset variables which store the escape code string appended to whilst parsing <escapeCode>, and the variable which records if the parse is running in <escaped> mode.
            escapeCode = "";
            escaped = false;

            // If there is a sauce record...
            if (file.sauce) {
                // Do a weak sanity check to see if there is a valid column setting, and use it if it passes.
                if (file.sauce.tInfo1 > 0 && file.sauce.tInfo1 <= 1000) {
                    columns = file.sauce.tInfo1;
                } else {
                    columns = 80;
                }
                // If no-blink mode is set in the sauce flags, use it. Otherwise, default to <options.icecolors> setting.
                icecolors = file.sauce.flags & 1 || options.icecolors;
            } else {
                // If "ced" mode has been invoked, set the <columns> to 78 character wide. Otherwise, use the default 80.
                if (options.mode === "ced") {
                    columns = 78;
                } else {
                    columns = 80;
                }
                // Set <icecolors> to whatever was chosen by the user, or set as the default by readBytes().
                icecolors = options.icecolors;
            }

            // Create the ScreenData() object at the required width.
            imageData = new ScreenData(columns);
            imageData.font = Font.preset(options.font, options);

            // Choose the correct Palette constant, depending on whichever mode has been set. See Palette for more information.
            switch (options.bits) {
            case "ced":
                imageData.palette = Palette.CED;
                break;
            case "workbench":
                imageData.palette = Palette.WORKBENCH;
                break;
            default:
                imageData.palette = Palette.ANSI;
            }

            // Returns an array of values found in <escapeCode>, seperated by ";". If there value is not a number, or missing, then the default value of 1 is used.
            function getValues() {
                return escapeCode.substr(1, escapeCode.length - 2).split(";").map(function (value) {
                    var parsedValue;
                    parsedValue = parseInt(value, 10);
                    return isNaN(parsedValue) ? 1 : parsedValue;
                });
            }

            while (!file.eof()) {
                // Obtain the current character <code>.
                code = file.get();
                if (escaped) {
                    // If the routine is in <escaped> mode, add the <code> to the <escapeCode> string.
                    escapeCode += String.fromCharCode(code);
                    // If the code terminates the <escaped> mode...
                    if ((code >= 65 && code <= 90) || (code >= 97 && code <= 122)) {
                        // ... set the mode to unescaped, and obtain the values in the escaped string.
                        escaped = false;
                        values = getValues();
                        // Check for a valid CSI code.
                        if (escapeCode.charAt(0) === "[") {
                            switch (escapeCode.charAt(escapeCode.length - 1)) {
                            case "A": // Up cursor.
                                y = Math.max(1, y - values[0]);
                                break;
                            case "B": // Down cursor.
                                y = Math.min(26 - 1, y + values[0]);
                                break;
                            case "C": // Forward cursor.
                                if (x === columns) {
                                    newLine();
                                }
                                x = Math.min(columns, x + values[0]);
                                break;
                            case "D": // Backward cursor.
                                x = Math.max(1, x - values[0]);
                                break;
                            case "H": // Set the cursor position by calling setPos(), first <y>, then <x>.
                                if (values.length === 1) {
                                    setPos(1, values[0]);
                                } else {
                                    setPos(values[1], values[0]);
                                }
                                break;
                            case "J": // Clear screen.
                                if (values[0] === 2) {
                                    x = 1;
                                    y = 1;
                                    imageData.reset();
                                }
                                break;
                            case "K": // Clear until the end of line.
                                for (j = x - 1; j < columns; ++j) {
                                    imageData.set(j, y - 1 + topOfScreen, 0, false, 0, 0);
                                }
                                break;
                            case "m": // Attributes, work through each code in turn.
                                for (j = 0; j < values.length; ++j) {
                                    if (values[j] >= 30 && values[j] <= 37) {
                                        // Set the <foreground> color, points to a value in the <palette> array...
                                        foreground = values[j] - 30;
                                        if (foreground24bit) {
                                            foreground24bit = undefined;
                                        }
                                    } else if (values[j] >= 40 && values[j] <= 47) {
                                        // ... and for <background>, if the required value is used.
                                        background = values[j] - 40;
                                        if (background24bit) {
                                            background24bit = undefined;
                                        }
                                    } else {
                                        switch (values[j]) {
                                        case 0: // Reset attributes
                                            resetAttributes();
                                            break;
                                        case 1: // Bold
                                            bold = true;
                                            if (foreground24bit) {
                                                foreground24bit = undefined;
                                            }
                                            break;
                                        case 5: // Blink
                                            blink = true;
                                            break;
                                        case 7: // Inverse
                                            inverse = true;
                                            break;
                                        case 22: // Bold off
                                            bold = false;
                                            break;
                                        case 25: // Blink off
                                            blink = false;
                                            break;
                                        case 27: // Inverse off
                                            inverse = false;
                                            break;
                                        }
                                    }
                                }
                                break;
                            case "s": // Save the current <x> and <y> positions.
                                savedX = x;
                                savedY = y;
                                break;
                            case "t": // 24 bit ANSI
                                if (values.length === 4) {
                                    switch (values[0]) {
                                    case 0: // Background
                                        background24bit = new Uint8Array([values[1], values[2], values[3]]);
                                        break;
                                    case 1: // Foreground
                                        foreground24bit = new Uint8Array([values[1], values[2], values[3]]);
                                        break;
                                    }
                                }
                                break;
                            case "u": // Restore the current <x> and <y> positions.
                                x = savedX;
                                y = savedY;
                                break;
                            }
                        }
                        // Finally, reset the <escapeCode>.
                        escapeCode = "";
                    }
                } else {
                    // If not in <escaped> mode, treat <code> as a literal.
                    switch (code) {
                    case 10: // Lone linefeed (LF).
                        newLine();
                        break;
                    case 13: // Carriage Return, and Linefeed (CRLF)
                        if (file.peek() === 0x0A) {
                            file.read(1);
                            newLine();
                        }
                        break;
                    case 26: // Ignore eof characters until the actual end-of-file, or sauce record has been reached.
                        break;
                    default:
                        // Go in <escaped> mode if "Esc[" is seen.
                        if (code === 27 && file.peek() === 0x5B) {
                            escaped = true;
                        } else {
                            // If "ced" mod has been invoked, don't record any additional attribute data.
                            if (options.mode === "ced") {
                                imageData.set(x - 1, y - 1 + topOfScreen, code, false, 1, 0);
                            } else {
                                // In <inverse> mode, or not, set the character <code> and attribute data to the <imageData> object, according to the current <foreground>, <background>, <icecolors>, <bold>, and <blink> setting.
                                if (inverse) {
                                    drawForeground = background;
                                    drawBackground = foreground;
                                } else {
                                    drawForeground = foreground;
                                    drawBackground = background;
                                }
                                if (bold) {
                                    drawForeground += 8;
                                }
                                if (blink && icecolors && !background24bit) {
                                    drawBackground += 8;
                                }
                                if (foreground24bit || background24bit) {
                                    imageData.set(x - 1, y - 1 + topOfScreen, code, true, foreground24bit || imageData.palette[drawForeground], background24bit || imageData.palette[drawBackground]);
                                } else {
                                    imageData.set(x - 1, y - 1 + topOfScreen, code, false, drawForeground, drawBackground);
                                }
                            }
                            // If the end of row has been reached, start a new line.
                            if (++x === columns + 1) {
                                newLine();
                            }
                        }
                    }
                }
            }

            // Returns an object usable by display() to convert into an RGBA array.
            return {
                "imageData": imageData,
                "sauce": file.sauce // SAUCE record.
            };
        }

        // A function to parse a sequence of bytes representing an ASCII plain-text file.
        function asc(bytes, options) {
            var file, imageData, code, x, y;

            // Create a new <file> object, based on <bytes>, and create an <imageData> representation of the screen.
            file = new File(bytes);
            imageData = new ScreenData(80);
            imageData.font = Font.preset(options.font, options);
            imageData.palette = Palette.ASC_PC;

            // Initialize the cursor position by setting <x> and <y>.
            x = 0;
            y = 0;

            while (!file.eof()) {
                // Get the character <code>
                code = file.get();
                // If we see a carriage return then line feed (CRLF), start a new line.
                if (code === 13 && file.peek() === 10) {
                    file.read(1);
                    ++y;
                    x = 0;
                } else if (code === 10) { // A lone line feed (LF) also starts a new line.
                    ++y;
                    x = 0;
                } else {
                    // For a literal, record the character code at the <x> and <y>.
                    imageData.set(x, y, code, false, 1, 0);
                    // Start a new line when columns is reached.
                    if (++x === 80) {
                        ++y;
                        x = 0;
                    }
                }
            }

            // Returns an object usable by display() to convert into an RGBA array.
            return {
                "imageData": imageData,
                "sauce": file.sauce // SAUCE record.
            };
        }

        // A function to parse a sequence of bytes representing a raw display dump.
        function bin(bytes, options) {
            var file, imageData, i, icecolors;

            // Create a new <file> object, based on <bytes>, and create an <imageData> representation of the screen.
            file = new File(bytes);

            imageData = new ScreenData(options.columns);
            imageData.font = Font.preset(options.font, options);
            imageData.palette = Palette.BIN;

            // Raw Imagedata.
            imageData.raw(file.read());

            // If there is sauce record, look for an <icecolors> setting in flags, use the user-defined or default setting if not.
            if (file.sauce) {
                icecolors = file.sauce.flags & 1 || options.icecolors;
            } else {
                icecolors = options.icecolors;
            }

            // If <icecolors> is turned off, make sure the attribute data is corrected to remove the background bright bit.
            if (!icecolors) {
                for (i = 1; i < imageData.length; i += 2) {
                    imageData[i] = imageData[i] & 127;
                }
            }

            // Returns an object usable by display() to convert into an RGBA array.
            return {
                "imageData": imageData,
                "sauce": file.sauce // SAUCE record.
            };
        }

        // A function to parse a sequence of bytes representing an iCE Draw file format.
        function idf(bytes, options) {
            var file, columns, imageData, c, loop, ch, attr, x, y;

            // Convert the bytes to a File() object.
            file = new File(bytes);

            // Seek to the column setting, and store.
            file.seek(8);
            columns = file.get16() + 1;

            // Create the <screenData> based on the column width.
            imageData = new ScreenData(columns);

            // Seek to the raw image data, and decode based on a run length encoding method.
            file.seek(12);

            x = 0;
            y = 0;
            while (file.getPos() < file.size - 4144) {
                c = file.get16();
                if (c === 1) {
                    loop = file.get();
                    file.get();
                    ch = file.get();
                    attr = file.get();
                    while (loop-- > 0) {
                        imageData.set(x++, y, ch, false, attr & 15, attr >> 4);
                        if (x === columns) {
                            x = 0;
                            ++y;
                        }
                    }
                } else {
                    imageData.set(x++, y, c & 255, false, (c >> 8) & 15, c >> 12);
                    if (x === columns) {
                        x = 0;
                        ++y;
                    }
                }
            }

            // Decode the font and palette data.
            imageData.font = Font.font8x16x256(file, options);
            imageData.palette = Palette.triplets16(file);

            return {
                "imageData": imageData,
                "sauce": file.sauce // The SAUCE record.
            };
        }

        // A function to parse a sequence of bytes representing PCBoard file format.
        function pcb(bytes, options) {
            var file, loop, charCode, bg, fg, icecolors, x, y, imageData;

            // Convert bytes into a File() object, only for the convenience of later extracting the sauce record.
            file = new File(bytes);
            imageData = new ScreenData(80);
            imageData.font = Font.preset(options.font, options);
            imageData.palette = Palette.BIN;

            // Reset all colour attributes, <bg> and <fg> and cursor positions, <x> and <y>.
            bg = 0;
            fg = 7;
            x = 0;
            y = 0;

            // Set <icecolors> depending on the setting of flags in the sauce record
            if (file.sauce) {
                icecolors = file.sauce.flags & 1 || options.icecolors;
            } else {
                icecolors = options.icecolors;
            }

            // Convenient function, to insert the current character code, <charCode>, with foreground and background attributes, <fg> and <bg>, at the current cursor position, <x> and <y>.
            function printChar() {
                imageData.set(x, y, charCode, false, fg, bg);
                if (++x === 80) {
                    y++;
                    x = 0;
                }
            }

            // Start the image data decoding loop
            loop = 0;
            while (loop < file.size) {
                // <charCode>, the current character under inspection.
                charCode = bytes[loop];

                // Exit if we encounter an EOF character.
                if (charCode === 26) {
                    break;
                }

                switch (charCode) {
                case 13: // Ignore Carriage Returns <CR>
                    break;
                case 10: // Linefeed character (LF), start a new line.
                    y++;
                    x = 0;
                    break;
                case 9: // Horizontal tabs, add spaces.
                    x += 8;
                    break;
                case 64: // If we have a control code...
                     // ... look ahead to see if it for and attribute change...
                    if (bytes[loop + 1] === 88) {
                        bg = bytes[loop + 2] - ((bytes[loop + 2] >= 65) ? 55 : 48);
                        if (!icecolors && bg > 7) {
                            bg -= 8;
                        }
                        fg = bytes[loop + 3] - ((bytes[loop + 3] >= 65) ? 55 : 48);
                        loop += 3;
                        // ... or to clear the screen...
                    } else if (bytes[loop + 1] === 67 && bytes[loop + 2] === 76 && bytes[loop + 3] === 83) {
                        x = y = 0;
                        imageData.reset();
                        loop += 4;
                        // ... or to set the cursor position.
                    } else if (bytes[loop + 1] === 80 && bytes[loop + 2] === 79 && bytes[loop + 3] === 83 && bytes[loop + 4] === 58) {
                        if (bytes[loop + 6] === 64) {
                            x = ((bytes[loop + 5]) - 48) - 1;
                            loop += 5;
                        } else {
                            x = (10 * ((bytes[loop + 5]) - 48) + (bytes[loop + 6]) - 48) - 1;
                            loop += 6;
                        }
                        // Otherwise, treat the control code as a literal.
                    } else {
                        printChar();
                    }
                    break;
                default: // Handle a literal character.
                    printChar();
                }
                loop++;
            }

            return {
                "imageData": imageData,
                "sauce": file.sauce // The sauce record.
            };
        }

        // A function to parse a sequence of bytes representing a Tundra file format.
        function tnd(bytes, options) {
            var file, x, y, imageData, charCode, fg, bg;

            // Routine to retrieve a 32-bit unsigned integer from a <file object>
            function get32(file) {
                var value;
                value = file.get() << 24;
                value += file.get() << 16;
                value += file.get() << 8;
                return value + file.get();
            }

            // Convert the bytes into a File() object;
            file = new File(bytes);

            // THrow an error if the magic number in the header isn't seen.
            if (file.get() !== 24) {
                throw "File ID does not match.";
            }
            if (file.getS(8) !== "TUNDRA24") {
                throw "File ID does not match.";
            }

            // Since Tundra files use 24-bit palettes, setup the foreground and background variables, <fg> and <bg>, as RGB arrays, and initialize the cursor positions.
            fg = new Uint8Array(3);
            bg = new Uint8Array(3);
            x = 0;
            y = 0;

            // Create the <imageData> object, as a 24-bit version.
            imageData = new ScreenData(80);
            imageData.font = Font.preset(options.font, options);
            imageData.palette = Palette.ANSI;

            while (!file.eof()) {
                // Start a newline if the current <x> position exceeds the column width.
                if (x === 80) {
                    x = 0;
                    ++y;
                }
                // Fetch the next character for inspection.
                charCode = file.get();
                // Cursor positioning code.
                if (charCode === 1) {
                    y = get32(file);
                    x = get32(file);
                }
                // Foreground attribute code.
                if (charCode === 2) {
                    charCode = file.get();
                    file.get();
                    fg.set(file.read(3), 0);
                }
                // Background attribute code.
                if (charCode === 4) {
                    charCode = file.get();
                    file.get();
                    bg.set(file.read(3), 0);
                }
                // Both foreground and background setting code.
                if (charCode === 6) {
                    charCode = file.get();
                    file.get();
                    fg.set(file.read(3), 0);
                    file.get();
                    bg.set(file.read(3), 0);
                }
                // In case we see a literal, print it (<charCode>), with the current foreground and background attributes, <fg> and <bg>.
                if (charCode !== 1 && charCode !== 2 && charCode !== 4 && charCode !== 6) {
                    imageData.set(x, y, charCode, true, fg, bg);
                    ++x;
                }
            }

            return {
                "imageData": imageData,
                "sauce": file.sauce // The sauce record.
            };
        }

        // A function to parse a sequence of bytes representing an XBiN file format.
        function xb(bytes, options) {
            var file, header, imageData;

            // This function is called to parse the XBin header.
            function XBinHeader(file) {
                var flags;

                // Look for the magic number, throw an error if not found.
                if (file.getS(4) !== "XBIN") {
                    throw "File ID does not match.";
                }
                if (file.get() !== 26) {
                    throw "File ID does not match.";
                }

                // Get the dimensions of the image...
                this.width = file.get16();
                this.height = file.get16();

                // ... and the height of the font, if included.
                this.fontHeight = file.get();

                //  Sanity check for the font height, throw an error if failed.
                if (this.fontHeight === 0 || this.fontHeight > 32) {
                    throw "Illegal value for the font height (" + this.fontHeight + ").";
                }

                // Retrieve the flags.
                flags = file.get();

                // Check to see if a palette and font is included.
                this.palette = ((flags & 1) === 1);
                this.font = ((flags & 2) === 2);

                // Sanity check for conflicting information in font settings.
                if (this.fontHeight !== 16 && !this.font) {
                    throw "A non-standard font size was defined, but no font information was included with the file.";
                }

                // Check to see if the image data is <compressed>, if non-blink mode is set, <nonBlink>, and if 512 characters are included with the font data. <char512>.
                this.compressed = ((flags & 4) === 4);
                this.nonBlink = ((flags & 8) === 8);
                this.char512 = ((flags & 16) === 16);
            }

            // Routine to decompress data found in an XBin <file>, which contains a Run-Length encoding scheme. Needs to know the current <width> and <height> of the image.
            function uncompress(file, width, height) {
                var uncompressed, p, i, j, repeatAttr, repeatChar, count;
                // Initialize the data used to store the image, each text character has two bytes, one for the character code, and the other for the attribute.
                uncompressed = new Uint8Array(width * height * 2);
                i = 0;
                while (i < uncompressed.length) {
                    p = file.get(); // <p>, the current code under inspection.
                    count = p & 63; // <count>, the times data is repeated
                    switch (p >> 6) { // Look at which RLE scheme to use
                    case 1: // Handle repeated character code.
                        for (repeatChar = file.get(), j = 0; j <= count; ++j) {
                            uncompressed[i++] = repeatChar;
                            uncompressed[i++] = file.get();
                        }
                        break;
                    case 2: // Handle repeated attributes.
                        for (repeatAttr = file.get(), j = 0; j <= count; ++j) {
                            uncompressed[i++] = file.get();
                            uncompressed[i++] = repeatAttr;
                        }
                        break;
                    case 3: // Handle repeated character code and attributes.
                        for (repeatChar = file.get(), repeatAttr = file.get(), j = 0; j <= count; ++j) {
                            uncompressed[i++] = repeatChar;
                            uncompressed[i++] = repeatAttr;
                        }
                        break;
                    default: // Handle no RLE.
                        for (j = 0; j <= count; ++j) {
                            uncompressed[i++] = file.get();
                            uncompressed[i++] = file.get();
                        }
                    }
                }
                return uncompressed; // Return the final, <uncompressed> data.
            }

            // Convert the bytes to a File() object, and reader the settings in the header, by calling XBinHeader().
            file = new File(bytes);
            header = new XBinHeader(file);

            // Fetch the image data, and uncompress if necessary.
            imageData = new ScreenData(header.width);

            // If palette information is included, read it immediately after the header, if not, use the default palette used for BIN files.
            imageData.palette = header.palette ? Palette.triplets16(file) : Palette.BIN;
            // If font information is included, read it, if not, use the default 80x25 font.
            imageData.font = header.font ? Font.xbin(file, header.fontHeight, options) : Font.preset("80x25", options);

            if (header.compressed) {
                imageData.raw(uncompress(file, header.width, header.height));
            } else {
                imageData.raw(file.read(header.width * header.height * 2));
            }

            return {
                "imageData": imageData,
                "sauce": file.sauce // The sauce record.
            };
        }

        // Parses an array of <bytes>, which represent a file, and calls <callback> when the image has been generated successfully, <splitRows> is set to a value greater than 0 if the image is to be split over multiple images, defined by an amount of rows. And <options> is key-pair list of options supplied by the user.
        function readBytes(bytes, callback, splitRows, options) {
            var data, returnArray, start, displayData;

            // Validate the options given by the user.
            options = validateOptions(options);

            // Choose which parser to use, based on the setting defined in <options.filetype>.
            switch (options.filetype) {
            case "txt":
            case "nfo":
            case "asc":
                // For plain-text files, use the ascii parser, and use the default, or user-defined font.
                data = asc(bytes, options);
                break;
            case "diz":
            case "ion":
                // For diz files, use the ascii parser, and use the default, or user-defined font. Also, trim the extra columns.
                data = asc(bytes, options);
                data.imageData.trimColumns();
                break;
            case "adf":
                // For Artworx files, use the adf parser. Font is already defined in the file.
                data = adf(bytes, options);
                break;
            case "bin":
                // For raw-dump files, use the bin parser, and use the default, or user-defined font.
                data = bin(bytes, options);
                break;
            case "idf":
                // For iCE draw files, use the idf parser. Font is already defined in the file.
                data = idf(bytes, options);
                break;
            case "pcb":
                // For PCBoard files, use the pcb parser, and use the default, or user-defined font.
                data = pcb(bytes, options);
                break;
            case "tnd":
                // For Tundra files, use the tnd parser, and use the default, or user-defined font.
                data = tnd(bytes, options);
                break;
            case "xb":
                // For XBin files, use the xb parser. Font is already set in the parser.
                data = xb(bytes, options);
                break;
            default:
                // For unrecognised filetypes, use the ANSI parser.
                data = ans(bytes, options);
            }

            // If the splitRows value is set..
            if (splitRows > 0) {
                // .. intialize an array used to store the multiple images, and calculate the byte-length of each image.
                returnArray = [];
                for (start = 0; start < data.imageData.rows; start += splitRows) {
                    // Call display with each "chunk" of data.
                    displayData = display(data.imageData, start, splitRows, options);
                    // Push the either raw image data or a canvas of each image into the array, according to the <options.imagedata> setting...
                    returnArray.push(options.imagedata ? displayData : displayDataToCanvas(displayData));
                }
                // ... and return it.
                callback(returnArray, data.sauce);
            } else {
                // For a single image, send the data to display()...
                displayData = display(data.imageData, 0, data.imageData.rows, options);
                // ... and call callback() with either the raw data, or a canvas element, depending on the <options.imagedata> setting. 
                callback(options.imagedata ? displayData : displayDataToCanvas(displayData), data.sauce);
            }
        }

        // A single entrypoint for the Parser.
        return {
            "readBytes": readBytes
        };
    }());

    // Parses an array of <bytes>, calls <callback> upon success. Uses <options> supplied by the user, and calls <callbackFail>, when supplied, if an error is caught.
    function renderBytes(bytes, callback, options, callbackFail) {
        // Catch any errors.
        try {
            // call readBytes(), with 0 as the splitRows option, and create an empty object if options, is missing.
            Parser.readBytes(bytes, callback, 0, options);
        } catch (e) {
            if (callbackFail) {
                // If an error is caught, call callbackFail()...
                callbackFail(e);
            } else {
                // ... otherwise, just throw it back.
                throw e;
            }
        }
    }

    // Same as renderBytes(), but this fetches a <url> by calling httpGet(), instead of supplying raw bytes.
    function render(url, callback, options, callbackFail) {
        // Call httpGet() with the supplied <url>.
        httpGet(url, function (bytes) {
            // Create a blank <options> object, if one wasn't supplied.
            options = options || {};
            // Set the filetype option, based on the url, if one wasn't already set in <options>.
            if (!options.filetype) {
                options.filetype = url.split(".").pop().toLowerCase();
            }
            // Call the version of this function for <bytes>, with the Uint8Array data returned with httpGet().
            renderBytes(bytes, callback, options, callbackFail);
            // Pass <callbackFail> to httpGet(), in case the network request fails.
        }, callbackFail);
    }

    // Parses an array of <bytes>, calls <callback> upon success. Uses <options> supplied by the user, and calls <callbackFail>, when supplied, if an error is caught. Multiple images are produced, based on the <splitRows> setting, divided by the amount of rows specified.
    function splitRenderBytes(bytes, callback, splitRows, options, callbackFail) {
        // Catch any errors.
        try {
            // call readBytes(), with 27 as the default splitRows option, and create an empty object if options, is missing.
            Parser.readBytes(bytes, callback, splitRows || 27, options);
        } catch (e) {
            if (callbackFail) {
                // If an error is caught, call callbackFail()...
                callbackFail(e);
            } else {
                // ... otherwise, just throw it back.
                throw e;
            }
        }
    }

    // Same as splitRenderBytes(), but this fetches a <url> by calling httpGet(), instead of supplying raw bytes.
    function splitRender(url, callback, splitRows, options, callbackFail) {
        // Call httpGet() with the supplied <url>.
        httpGet(url, function (bytes) {
            // Create a blank <options> object, if one wasn't supplied.
            options = options || {};
            // Set the filetype option, based on the url, if one wasn't already set in <options>.
            if (!options.filetype) {
                options.filetype = url.split(".").pop().toLowerCase();
            }
            // Call the version of this function for <bytes>, with the Uint8Array data returned with httpGet().
            splitRenderBytes(bytes, callback, splitRows, options, callbackFail);
            // Pass <callbackFail> to httpGet(), in case the network request fails.
        }, callbackFail);
    }

    // Receives a sequence of <bytes>, representing an ANSI file, with <options> supplied by the user and returns an Ansimation object which can be used to display and control an animation.
    function Ansimation(bytes, options) {
        var timer, interval, file, font, palette, columns, rows, canvas, ctx, blinkCanvas, buffer, bufferCtx, blinkCtx, escaped, escapeCode, j, code, values, x, y, savedX, savedY, foreground, background, foreground24bit, background24bit, drawForeground, drawBackground, bold, inverse, blink, fontImageData;

        // Convert bytes to a File() object.
        file = new File(bytes);

        options = validateOptions(options);

        switch (options.bits) {
        case "ced":
            palette = Palette.CED;
            break;
        case "workbench":
            palette = Palette.WORKBENCH;
            break;
        default:
            palette = Palette.ANSI;
        }

        // If the <columns> setting in the SAUCE record is set, use it.
        if (file.sauce && file.sauce.tInfo1 > 0) {
            columns = file.sauce.tInfo1;
        } else if (options.mode === "ced") {
            columns = 78;
        } else {
            columns = 80;
        }

        // Set the amount of <rows> is set in <options>, use it.
        rows = options.rows || 26;

        // Use the <font> set in <options>, if found in presets, otherwise use the default "80x25".
        font = Font.has(options.font) ? Font.preset(options.font, options) : Font.preset("80x25", options);

        // Initialize the canvas used to display the animation, obtain the context, and create the temporary variable <fontImageData> to store the font image-data when rendered.
        canvas = createCanvas(columns * font.width, rows * font.height);

        // Deal with pixel ratio for retina-type displays.
        if (options["2x"]) {
            canvas.style.width = (canvas.width / 2) + "px";
            canvas.style.height = (canvas.height / 2) + "px";
        }

        ctx = canvas.getContext("2d");
        fontImageData = ctx.createImageData(font.width, font.height);

        // <blinkCanvas> is used to record the blinking "on" and "off" on two seperate images, which are then composited onto the main <canvas> alternately.
        blinkCanvas = [createCanvas(canvas.width, canvas.height), createCanvas(canvas.width, canvas.height)];
        buffer = createCanvas(canvas.width, canvas.height);
        blinkCtx = blinkCanvas.map(function (canvas) {
            return canvas.getContext("2d");
        });
        bufferCtx = buffer.getContext("2d");

        // Reset all the text attributes set by ANSI control codes.
        function resetAttributes() {
            foreground = 7;
            background = 0;
            foreground24bit = undefined;
            background24bit = undefined;
            bold = false;
            blink = false;
            inverse = false;
        }

        // Clear all the screen data, on all canvases, including the <blinkCanvas> array.
        function clearScreen(sx, sy, width, height) {
            ctx.fillStyle = "rgb(" + palette[0][0] + ", " + palette[0][1] + ", " + palette[0][2] + ")";
            ctx.fillRect(sx, sy, width, height);
            blinkCtx[0].clearRect(sx, sy, width, height);
            blinkCtx[1].clearRect(sx, sy, width, height);
        }

        // Clear the text characters held on the <blinkCanvas> array, used when a character is drawn which isn't set to blink.
        function clearBlinkChar(charX, charY) {
            var sx, sy;
            sx = charX * font.width;
            sy = charY * font.height;
            blinkCtx[0].clearRect(sx, sy, font.width, font.height);
            blinkCtx[1].clearRect(sx, sy, font.width, font.height);
        }

        // Perform a newline operation, if the <y> amount is at the very bottom of the screen, then all canvas elements are shifted up a single line.
        function newLine() {
            x = 1;
            if (y === rows - 1) {
                ctx.drawImage(canvas, 0, font.height, canvas.width, canvas.height - font.height * 2, 0, 0, canvas.width, canvas.height - font.height * 2);
                bufferCtx.clearRect(0, 0, canvas.width, canvas.height);
                bufferCtx.drawImage(blinkCanvas[0], 0, font.height, canvas.width, canvas.height - font.height * 2, 0, 0, canvas.width, canvas.height - font.height * 2);
                blinkCtx[0].clearRect(0, 0, canvas.width, canvas.height);
                blinkCtx[0].drawImage(buffer, 0, 0);
                bufferCtx.clearRect(0, 0, canvas.width, canvas.height);
                bufferCtx.drawImage(blinkCanvas[1], 0, font.height, canvas.width, canvas.height - font.height * 2, 0, 0, canvas.width, canvas.height - font.height * 2);
                blinkCtx[1].clearRect(0, 0, canvas.width, canvas.height);
                blinkCtx[1].drawImage(buffer, 0, 0);
                clearScreen(0, canvas.height - font.height * 2, canvas.width, font.height);
                return true;
            }
            ++y;
            return false;
        }

        // Sets the cursor position, <x> and <y>, according to new values. Performs a validation to make sure it remains in the boundries of the canvas.
        function setPos(newX, newY) {
            x = Math.min(columns, Math.max(1, newX));
            y = Math.min(rows, Math.max(1, newY));
        }

        // Resets all the settings, used upon initialization, and to restore after an animation is restarted.
        function resetAll() {
            clearScreen(0, 0, canvas.width, canvas.height);
            resetAttributes();
            setPos(1, 1);
            escapeCode = "";
            escaped = false;
            file.seek(0);
        }

        resetAll();

        // Obtains all the values currently stores in an <escapeCode> string. If one of the values cannot be parsed by parseInt(), or is missing, then the default value of 1 is used.
        function getValues() {
            return escapeCode.substr(1, escapeCode.length - 2).split(";").map(function (value) {
                var parsedValue;
                parsedValue = parseInt(value, 10);
                return isNaN(parsedValue) ? 1 : parsedValue;
            });
        }

        // Reads a certain amount of bytes, <num>, from the <file> object.
        function read(num) {
            var i;
            for (i = 0; i < num; ++i) {
                // Break out of the loop if the end of file has been reached.
                if (file.eof()) {
                    break;
                }
                // Store the current character fro inspection in <code>.
                code = file.get();
                if (escaped) {
                    // If the <escaped> mode is set, add the code to <escapeCode> string.
                    escapeCode += String.fromCharCode(code);
                    // If the character ends the <escapeCode> string...
                    if ((code >= 65 && code <= 90) || (code >= 97 && code <= 122)) {
                        // Turn <escaped> mode off, and obtain the values in the <escapeCode> string.
                        escaped = false;
                        values = getValues();
                        // For ANSI control codes.
                        if (escapeCode.charAt(0) === "[") {
                            switch (escapeCode.charAt(escapeCode.length - 1)) {
                            case "A": // Cursor up.
                                y = Math.max(1, y - values[0]);
                                break;
                            case "B": // Cursor down.
                                y = Math.min(rows - 1, y + values[0]);
                                break;
                            case "C": // Cursor right, creating a newline if necessary.
                                if (x === columns) {
                                    if (newLine()) {
                                        // Break out of the loop if the canvas has been shifted up, this causes the screen to be updated after breaking out of the loop to create the effect of smooth scrolling.
                                        return i + 1;
                                    }
                                }
                                x = Math.min(columns, x + values[0]);
                                break;
                            case "D": // Cursor Up.
                                x = Math.max(1, x - values[0]);
                                break;
                            case "H": // Set the cursor position, default value of 1 for <x> if missing.
                                if (values.length === 1) {
                                    setPos(1, Math.min(values[0]));
                                } else {
                                    setPos(values[1], values[0]);
                                }
                                break;
                            case "J": // Clear screen, if allowed in <options["2J"]>
                                if (options["2J"] && values[0] === 2) {
                                    x = 1;
                                    y = 1;
                                    clearScreen(0, 0, canvas.width, canvas.height);
                                }
                                break;
                            case "K": // Clear to the end of line.
                                clearScreen((x - 1) * font.width, (y - 1) * font.height, canvas.width - (x - 1) * font.width, font.height);
                                break;
                            case "m": // Attribute setting codes.
                                for (j = 0; j < values.length; ++j) {
                                    if (values[j] >= 30 && values[j] <= 37) {
                                        // Set the foreground colour.
                                        foreground = values[j] - 30;
                                        if (foreground24bit) {
                                            foreground24bit = undefined;
                                        }
                                    } else if (values[j] >= 40 && values[j] <= 47) {
                                        // Set the background colour.
                                        background = values[j] - 40;
                                        if (background24bit) {
                                            background24bit = undefined;
                                        }
                                    } else {
                                        switch (values[j]) {
                                        case 0: // Reset attributes.
                                            resetAttributes();
                                            break;
                                        case 1: // Bold on.
                                            bold = true;
                                            if (foreground24bit) {
                                                foreground24bit = undefined;
                                            }
                                            break;
                                        case 5: // Blink on.
                                            blink = true;
                                            break;
                                        case 7: // Inverse on.
                                            inverse = true;
                                            break;
                                        case 22: // Bold off.
                                            bold = false;
                                            break;
                                        case 25: // Blink off.
                                            blink = false;
                                            break;
                                        case 27: // Inverse off.
                                            inverse = false;
                                            break;
                                        }
                                    }
                                }
                                break;
                            case "s": // Store the current cursor position.
                                savedX = x;
                                savedY = y;
                                break;
                            case "t": // 24 bit ANSI
                                if (values.length === 4) {
                                    switch (values[0]) {
                                    case 0: // Background
                                        background24bit = new Uint8Array([values[1], values[2], values[3], 255]);
                                        break;
                                    case 1: // Foreground
                                        foreground24bit = new Uint8Array([values[1], values[2], values[3], 255]);
                                        break;
                                    }
                                }
                                break;
                            case "u": // Restore the saved cursor position.
                                if (savedX !== undefined && savedY !== undefined) {
                                    x = savedX;
                                    y = savedY;
                                }
                                break;
                            }
                        }
                        escapeCode = "";
                    }
                } else {
                    switch (code) {
                    case 10: // For a lone line feed (LF), start a new line.
                        // Break out of the loop if the canvas has been shifted up, this causes the screen to be updated after breaking out of the loop to create the effect of smooth scrolling.
                        if (newLine()) {
                            // Return how many characters were interpreted.
                            return i + 1;
                        }
                        break;
                    case 13:
                        // If a carriage return and line feed are seen together (CRLF), treat as a newline.
                        if (file.peek() === 0x0A) {
                            file.read(1);
                            // Break out of the loop if the canvas has been shifted up, this causes the screen to be updated after breaking out of the loop to create the effect of smooth scrolling.
                            if (newLine()) {
                                // Return how many characters were interpreted.
                                return i + 1;
                            }
                        }
                        break;
                    case 26: // Ignore eof characters.
                        break;
                    default: // Deal with literals
                        // If an ANSI control code is seen, go into <escaped> mode.
                        if (code === 27 && file.peek() === 0x5B) {
                            escaped = true;
                        } else {
                            // Swap colours is <inverse> is set, otherwise, do not.
                            if (inverse) {
                                drawForeground = background;
                                drawBackground = foreground;
                            } else {
                                drawForeground = foreground;
                                drawBackground = background;
                            }
                            // Shift the colours is <bold> is set, observing the current <options.icecolors> setting.
                            if (bold) {
                                drawForeground += 8;
                            }
                            if (blink && options.icecolors && !background24bit) {
                                drawBackground += 8;
                            }
                            // Obtain the <fontImageData> by calling font.getData().
                            if (foreground24bit || background24bit) {
                                fontImageData.data.set(font.get24BitData(code, foreground24bit || palette[drawForeground], background24bit || palette[drawBackground]), 0);
                            } else {
                                fontImageData.data.set(font.getData(code, palette, drawForeground, drawBackground), 0);
                            }
                            // Draw the image to the canvas.
                            ctx.putImageData(fontImageData, (x - 1) * font.width, (y - 1) * font.height, 0, 0, font.width, font.height);
                            if (!options.icecolors && !background24bit) {
                                // Update the blink canvas elements, by drawing both versions of the blinking data to the <blinkCanvas> array, or if <blink> is not set, clear whatever may already be drawn to these elements.
                                if (blink) {
                                    blinkCtx[0].putImageData(fontImageData, (x - 1) * font.width, (y - 1) * font.height, 0, 0, font.width, font.height);
                                    fontImageData.data.set(font.getData(code, palette, drawBackground, drawBackground), 0);
                                    blinkCtx[1].putImageData(fontImageData, (x - 1) * font.width, (y - 1) * font.height, 0, 0, font.width, font.height);
                                } else {
                                    clearBlinkChar(x - 1, y - 1);
                                }
                            }
                            // Start a new line if the <columns> boundry has been reached.
                            if (++x === columns + 1) {
                                // Break out of the loop if the canvas has been shifted up, this causes the screen to be updated after breaking out of the loop to create the effect of smooth scrolling.
                                if (newLine()) {
                                    // Return how many characters were interpreted.
                                    return i + 1;
                                }
                            }
                        }
                    }
                }
            }

            // Return how many characters were interpreted, if we return 0, then the end of file has been reached.
            return i;
        }

        // Starts playing the animation from <file> at the specified <baud> rate. Calls <callback> upon completion>, and only clears the screen when encountering "Esc[2J" if <clearScreen> is set to true.
        function play(baud, callback, clearScreen) {
            var length, drawBlink;
            // Sanity check for the <clearScreen> setting, defaults to true.
            clearScreen = (clearScreen === undefined) ? true : clearScreen;
            // Stop playing the animation, <timer>, and stops the blinking <interval> timer, if currently playing.
            clearTimeout(timer);
            clearInterval(interval);
            // <drawBlink> is used to select which <blinkCanvas> is drawn to the screen.
            drawBlink = false;
            // Start drawing each <blinkCanvas> to <canvas> alternately, every 250ms.
            interval = setInterval(function () {
                ctx.drawImage(blinkCanvas[drawBlink ? 1 : 0], 0, 0);
                drawBlink = !drawBlink;
            }, 250);
            // When called, drawChunk() will interpret and draw the next chunk of data, the maximum of <length> bytes long, by calling read(), every 10ms. If a value of 0 is returned by read(), call the <callback> function to indicate that it is complete.
            function drawChunk() {
                if (read(length)) {
                    timer = setTimeout(drawChunk, 10);
                } else if (callback) {
                    callback();
                }
            }
            // Calculate roughly how many bytes to draw, based on the <baud> setting.
            length = Math.floor((baud || 115200) / 8 / 100);
            // If <clearScreen> is set, then clear everything, otherwise, just reset all the attributes and escaped data.
            if (clearScreen) {
                resetAll();
            } else {
                resetAttributes();
                escapeCode = "";
                escaped = false;
                file.seek(0);
            }
            // Start interpreting the data.
            drawChunk();
        }

        // Stops interpreting data, and copying the <blinkCanvas> to <canvas>
        function stop() {
            clearTimeout(timer);
            clearInterval(interval);
        }

        // Sets <file> to a new array of <bytes>, so new data can be appended to the animation.
        function load(bytes, callback) {
            clearTimeout(timer);
            file = new File(bytes);
            callback(file.sauce);
        }

        // Returns the standard <canvas> and <sauce> information, as well as a <controller> object which is used to <play> and <stop> animations, as well as <load> new data.
        return {
            "canvas": canvas,
            "sauce": file.sauce,
            "controller": {
                "play": play,
                "stop": stop,
                "load": load
            }
        };
    }

    // animateBytes() returns a controller object used to control an <ansimation>, based on the supplied <bytes> and <options> provided by the user.
    function animateBytes(bytes, callback, options) {
        var ansimation;
        // Create the new ansimation object.
        ansimation = new Ansimation(bytes, options);
        // The reason for the timeout here is to return the controller object before calling <callback>, so that the animation isn't started before the controller is returned. Ideally, the controller should be passed via callback(), but it's implemented this way to achieve parity with the render() and splitRender() methods.
        setTimeout(function () {
            callback(ansimation.canvas, ansimation.sauce);
        }, 250);
        // Return the controller object.
        return ansimation.controller;
    }

    // The same as animateBytes(), but fetches <bytes> from a <url>, and calls <callbackFail> if it fails.
    function animate(url, callback, options, callbackFail) {
        var ansimation;
        // Fetch the data.
        httpGet(url, function (bytes) {
            ansimation = new Ansimation(bytes, options);
            callback(ansimation.canvas, ansimation.sauce);
            // Pass <callbackFail> to httpGet, in case it fails.
        }, callbackFail);
        // The reason a new controller object is created here, instead of passing <ansimation.controller> directly, is because <ansimation> isn't initialized until the bytes are received asynchronously, via httpGet().
        return {
            "play": function (baud, callback, clearScreen) {
                ansimation.controller.play(baud, callback, clearScreen);
            },
            "stop": function () {
                ansimation.controller.stop();
            },
            // In this version of load(), httpGet provides the bytes.
            "load": function (url, callback, callbackFail) {
                httpGet(url, function (bytes) {
                    ansimation.controller.load(bytes, callback);
                }, callbackFail);
            }
        };
    }

    // If this is running in a Web Worker instance, do not initialize Popup, as it provides an in-browser function.
    if (!self.WorkerLocation) {
        // Popup collects functions which allows a "pop-up" display to be shown in the browser, instead of calling the various render methods elsewhere.
        Popup = (function () {
            var STYLE_DEFAULTS;

            // Defaults used when rewriting the various CSS properties when creating a new element.
            STYLE_DEFAULTS = {"background-color": "transparent", "background-image": "none", "margin": "0", "padding": "0", "border": "0", "font-size": "100%", "font": "inherit", "vertical-align": "baseline", "color": "black", "display": "block", "cursor": "default", "text-align": "left", "text-shadow": "none", "text-transform": "none", "clear": "none", "float": "none", "overflow": "auto", "position": "relative", "visibility": "visible"};

            // Works through every element, and discovers the highest z-index recorded. Later used to make sure that elements added to the document are visible.
            function findHighestZIndex() {
                var elements, highest, i, zIndex;
                for (i = 0, elements = document.getElementsByTagName("*"), highest = 0; i < elements.length; ++i) {
                    zIndex = document.defaultView.getComputedStyle(elements[i]).zIndex;
                    if (zIndex !== "auto" && zIndex !== "inherit") {
                        highest = Math.max(highest, parseInt(zIndex, 10));
                    }
                }
                return highest;
            }

            // Applies styles to an <element> stored in an object <style>
            function applyStyle(element, style) {
                var name;
                for (name in style) {
                    if (style.hasOwnProperty(name)) {
                        // Mark every-one as "important", to make sure that it doesn't inherit any styles on the page.
                        element.style.setProperty(name, style[name], "important");
                    }
                }
            }

            // Creates a new "div" element, applies the default set of CSS properties, and applies an optional set from <style>.
            function createDiv(style) {
                var div;
                style = style || {};
                div = document.createElement("div");
                applyStyle(div, STYLE_DEFAULTS);
                applyStyle(div, style);
                return div;
            }

            // Sets the transition css properties to <element>, and applies a <style> immediately to perform a CSS transition after a short timeout (in order to make sure the transition styles are registered first).
            function transitionCSS(element, transProperty, transDuration, transFunction, style) {
                element.style.transitionProperty = transProperty;
                element.style.transitionDuration = transDuration;
                element.style.transitionTimingFunction = transFunction;
                if (style) {
                    setTimeout(function () {
                        applyStyle(element, style);
                    }, 50);
                }
            }

            // Displays a pop-up, based on the supplied <bytes> and <baud>-rate (if this is set to 0, display as an image). Also uses the user-supplied <options>.
            function show(bytes, baud, options) {
                var divOverlay, divCanvasContainer;

                // Slides up the <divOverlay> element on the screen by setting various transition styles, also displays a loading spinner, if a url is provided in <options.spinner>
                function slideUpContainer() {
                    if (options.spinner) {
                        applyStyle(divOverlay, {"background-image": "none"});
                    }
                    transitionCSS(divCanvasContainer, "top", "0.6s", "ease-in-out", {"top": "0"});
                    setTimeout(function () {
                        applyStyle(divOverlay, {"overflow": "auto"});
                    }, 750);
                }

                // Applies styles to a <canvas> element, also makes sure each <canvas> element is displayed vertically without a gap, by setting vertical-align: bottom.
                function processCanvas(canvas) {
                    // Apply default styles.
                    applyStyle(canvas, STYLE_DEFAULTS);
                    canvas.style.verticalAlign = "bottom";

                    return canvas;
                }

                // Displays an error, in the form of an dialog box, with a defined <message>, and dismisses the overlay element.
                function error(message) {
                    alert("Error: " + message);
                    document.body.removeChild(divOverlay);
                }

                // Removes the overlay element.
                function dismiss(evt) {
                    evt.preventDefault();
                    document.body.removeChild(divOverlay);
                }

                // Create the overlay element with various css styles.
                divOverlay = createDiv({"position": "fixed", "left": "0px", "top": "0px", "width": "100%", "height": "100%", "background-color": "rgba(0, 0, 0, 0.8)", "overflow": "hidden", "z-index": (findHighestZIndex() + 1).toString(10), "opacity": "0"});
                // If a spinner url is provided in <options>, add it to the backdrop of the overlay element...
                if (options.spinner) {
                    applyStyle(divOverlay, {"background-image": "url(" + options.spinner + ")", "background-position": "center center", "background-repeat": "no-repeat"});
                    // ... and scale it down to half-size in css-pixels if a retina-type is being used.
                    if (options["2x"]) {
                        applyStyle(divOverlay, {"background-size": "32px 64px"});
                    }
                }
                // Create the elemtn used to containt the canvas element(s).
                divCanvasContainer = createDiv({"background-color": "black", "box-shadow": "0 8px 32px rgb(0, 0, 0)", "margin": "8px auto", "padding": "16px", "border": "2px solid white", "border-radius": "8px", "top": "100%"});

                // Add the elements to the document.
                divOverlay.appendChild(divCanvasContainer);
                document.body.appendChild(divOverlay);

                // Add the transition properties, and start the transition.
                transitionCSS(divOverlay, "opacity", "0.2s", "ease-out", {"opacity": "1.0"});

                // After the transition has been given time to complete, start the rendering process.
                setTimeout(function () {
                    var controller;
                    // If a baud rate setting has been defined, regard as an animation.
                    if (baud > 0) {
                        controller = animateBytes(bytes, function (canvas) {
                            // Set the container's width based on the width of the canvas element, and display the canvas.
                            if (options["2x"]) {
                                divCanvasContainer.style.width = (canvas.width / 2) + "px";
                            } else {
                                divCanvasContainer.style.width = canvas.width + "px";
                            }
                            divCanvasContainer.appendChild(processCanvas(canvas));
                            // Slide up the container.
                            slideUpContainer();
                            setTimeout(function () {
                                // Start playing the animation after the sliding effect.
                                controller.play(baud);
                            }, 750);
                            // If the overlay is clicked anywhere...
                            divOverlay.onclick = function (evt) {
                                // ... dismiss the overlay, and stop the animation.
                                dismiss(evt);
                                controller.stop();
                            };
                        }, options); // Pass the options to animateBytes.
                    } else { // If no baud-rate, treat as an image.
                        splitRenderBytes(bytes, function (canvases) {
                            // Set the container's width based on the width of the first canvas element.
                            if (options["2x"]) {
                                divCanvasContainer.style.width = (canvases[0].width / 2) + "px";
                            } else {
                                divCanvasContainer.style.width = canvases[0].width + "px";
                            }
                            canvases.forEach(function (canvas) {
                                // Append each canvas element to the element container.
                                divCanvasContainer.appendChild(processCanvas(canvas));
                            });
                            // Slide up the container.
                            slideUpContainer();
                            // If the overlay is clicked anywhere dismiss the overlay.
                            divOverlay.onclick = dismiss;
                        }, 100, options, error); // Pass the options and error function to splitRenderBytes.
                    }
                }, 250);
            }

            // Single entrypoint for popup.
            return {
                "show": show
            };
        }());
    }

    // Calls show() in <Popup>, according to the supplied <bytes> and <options>.
    function popupBytes(bytes, options) {
        // Set baud-rate to 0, since this is assumed to be an image.
        Popup.show(bytes, 0, options);
    }

    // The <url> version of popupBytes(), which gets the <bytes> from a file from the network first, and calls <callbackFail> when the network fetch fails.
    function popup(url, options, callbackFail) {
        httpGet(url, function (bytes) {
            // Set <options> to an empty object, if not set.
            options = options || {};
            // Set the filetype to the url extension, if <options.filetype> is not already set.
            if (!options.filetype) {
                options.filetype = url.split(".").pop().toLowerCase();
            }
            // Call popupBytes() with the <bytes> returned from the httpGet() operation.
            popupBytes(bytes, options);
            // Pass <callbackFail> to httpGet(), in case the operation fails.
        }, callbackFail);
    }

    // The animation version of popupBytes(), this sets the <baud> option, defaults to 14400, so the bytes are assumend to represent an ANSI animation.
    function popupAnimationBytes(bytes, baud, options) {
        Popup.show(bytes, baud || 14400, options);
    }

    // The <url> version of popupAnimationBytes(), fetches the <bytes> from a httpGet() operation.
    function popupAnimation(url, baud, options, callbackFail) {
        httpGet(url, function (bytes) {
            // No filetype setting is set here, as the bytes are assumed in an animation to represent an ANSI file.
            popupAnimationBytes(bytes, baud, options);
            // Pass <callbackFail> to httpGet(), in case the operation fails.
        }, callbackFail);
    }

    // Return all the publicly-available functions for AnsiLove.
    return {
        "sauceBytes": sauceBytes,
        "sauce": sauce,
        // Used to convert raw image data to a canvas element, after a web worker returns it's results.
        "displayDataToCanvas": displayDataToCanvas,
        "renderBytes": renderBytes,
        "render": render,
        "splitRenderBytes": splitRenderBytes,
        "splitRender": splitRender,
        "animateBytes": animateBytes,
        "animate": animate,
        "popupBytes": popupBytes,
        "popup": popup,
        "popupAnimationBytes": popupAnimationBytes,
        "popupAnimation": popupAnimation
    };
}());

(function () {
    "use strict";
    // If this script is executed as part of a Web Worker thread, attach methods to <self> to provide hooks for a web worker instance.
    if (self.WorkerLocation) {
        self.onmessage = function (evt) {
            // If raw bytes have been supplied.
            if (evt.data.bytes) {
                if (evt.data.split > 0) { // If the imagedata is to be split.
                    // Web worker function for splitRenderBytes.
                    AnsiLove.splitRenderBytes(evt.data.bytes, function (imagedata, sauce) {
                        // Return the raw-data, returned by the display() function, and a sauce record.
                        self.postMessage({"splitimagedata": imagedata, "sauce": sauce});
                        // Pass the various options from the web worker invocation, setting the <imagedata> setting on.
                    }, evt.data.split, {"imagedata": 1, "font": evt.data.font, "bits": evt.data.bits, "icecolors": evt.data.icecolors, "columns": evt.data.columns, "thumbnail": evt.data.thumbnail, "2x": evt.data["2x"], "filetype": evt.data.filetype});
                } else { // For just a single image.
                    // Web worker function for renderBytes.
                    AnsiLove.renderBytes(evt.data.bytes, function (imagedata, sauce) {
                        // Return the raw-data, returned by the display() function, and a sauce record.
                        self.postMessage({"imagedata": imagedata, "sauce": sauce});
                        // Pass the various options from the web worker invocation, setting the <imagedata> setting on.
                    }, {"imagedata": 1, "font": evt.data.font, "bits": evt.data.bits, "icecolors": evt.data.icecolors, "columns": evt.data.columns, "thumbnail": evt.data.thumbnail, "2x": evt.data["2x"], "filetype": evt.data.filetype});
                }
            } else { // If a url has been supplied.
                if (evt.data.split > 0) { // If the imagedata is to be split.
                    AnsiLove.splitRender(evt.data.url, function (imagedata, sauce) {
                        // Return the raw-data, returned by the display() function, and a sauce record.
                        self.postMessage({"splitimagedata": imagedata, "sauce": sauce});
                        // Pass the various options from the web worker invocation, setting the <imagedata> setting on.
                    }, evt.data.split, {"imagedata": 1, "font": evt.data.font, "bits": evt.data.bits, "icecolors": evt.data.icecolors, "columns": evt.data.columns, "thumbnail": evt.data.thumbnail, "2x": evt.data["2x"], "filetype": evt.data.filetype});
                } else { // For just a single image.
                    AnsiLove.render(evt.data.url, function (imagedata, sauce) {
                        // Return the raw-data, returned by the display() function, and a sauce record.
                        self.postMessage({"imagedata": imagedata, "sauce": sauce});
                        // Pass the various options from the web worker invocation, setting the <imagedata> setting on.
                    }, {"imagedata": 1, "font": evt.data.font, "bits": evt.data.bits, "icecolors": evt.data.icecolors, "columns": evt.data.columns, "thumbnail": evt.data.thumbnail, "2x": evt.data["2x"], "filetype": evt.data.filetype});
                }
            }
        };
    }
}());