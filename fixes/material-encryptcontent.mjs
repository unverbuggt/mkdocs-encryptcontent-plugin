//tested with mkdocs-material 9.5.2
//this function is run by mkdocs-encryptcontent-plugin after successfull decryption
function theme_run_after_decryption() {
    document$.next(document);
}

window["theme_run_after_decryption"] = theme_run_after_decryption;
