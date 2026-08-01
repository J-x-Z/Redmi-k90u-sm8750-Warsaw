#include <linux/init.h>
#include <linux/module.h>

static int __init warsaw_kernelsu_sdk_smoke_init(void)
{
	return 0;
}

static void __exit warsaw_kernelsu_sdk_smoke_exit(void)
{
}

module_init(warsaw_kernelsu_sdk_smoke_init);
module_exit(warsaw_kernelsu_sdk_smoke_exit);

MODULE_DESCRIPTION("Warsaw KernelSU GKI external module SDK compile test");
MODULE_LICENSE("GPL");
